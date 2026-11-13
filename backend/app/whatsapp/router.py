"""WhatsApp Cloud API webhook.

GET  /api/whatsapp/webhook  - Meta checks the verify token once, when you save the webhook.
POST /api/whatsapp/webhook  - Meta sends every customer message here (signed with the app secret).

We answer Meta with 200 straight away and do the real work in the background,
because Meta retries (and sends duplicates) when a webhook is slow.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pymongo.errors import DuplicateKeyError

from app.config import Settings, get_settings
from app.db import db_dependency
from app.models import Enquiry
from app.notify import send_lead_notifications, send_telegram_photo, send_telegram_text
from app.phone import normalize_phone
from app.whatsapp import client
from app.whatsapp.flow import Inbound, handle

logger = logging.getLogger("anweshan.whatsapp")

whatsapp_router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

ECHO_PAUSE = timedelta(hours=24)  # owner replied by hand -> bot stays quiet in that chat
MAX_MESSAGE_AGE = timedelta(hours=6)  # very late deliveries are not answered by the bot
SEEN_TTL = timedelta(days=3)

_locks: dict[str, list] = {}  # wa_id -> [lock, number of tasks using it]


def _lock_for(wa_id: str) -> asyncio.Lock:
    """One lock per chat, so two quick messages (e.g. 3 photos) are handled one by one.
    Fine for a single Railway instance; with several instances use a DB lock instead."""
    item = _locks.get(wa_id)
    if item is None:
        item = _locks[wa_id] = [asyncio.Lock(), 0]
    item[1] += 1
    return item[0]


def _release_lock(wa_id: str) -> None:
    item = _locks.get(wa_id)
    if item is not None:
        item[1] -= 1
        if item[1] <= 0:
            _locks.pop(wa_id, None)


def valid_signature(raw: bytes, header: str | None, app_secret: str) -> bool:
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def parse_inbound(m: dict, name: str) -> Inbound:
    kind = m.get("type")
    if kind == "text":
        return Inbound("text", text=(m.get("text") or {}).get("body", "")[:2000], name=name)
    if kind == "interactive":
        inter = m.get("interactive") or {}
        reply = inter.get("button_reply") or inter.get("list_reply") or {}
        return Inbound("choice", text=reply.get("title", ""), choice_id=reply.get("id"), name=name)
    if kind == "button":  # quick-reply button on a template message
        return Inbound("text", text=(m.get("button") or {}).get("text", ""), name=name)
    if kind == "image":
        return Inbound("image", text=(m.get("image") or {}).get("caption", ""), name=name)
    if kind == "location":
        loc = m.get("location") or {}
        label = ", ".join(x for x in (loc.get("name"), loc.get("address")) if x)
        if not label and loc.get("latitude") is not None:
            label = f"https://maps.google.com/?q={loc.get('latitude')},{loc.get('longitude')}"
        return Inbound("location", text=label, name=name)
    return Inbound("other", name=name)


async def _owner_contact(db, settings: Settings) -> str | None:
    if settings.WA_OWNER_CONTACT:
        return settings.WA_OWNER_CONTACT
    site = await db.settings.find_one({"id": "site"}) or {}
    return site.get("phone") or None


async def _first_time(db, message_id: str, now: datetime) -> bool:
    try:
        res = await db.wa_seen.update_one(
            {"_id": message_id},
            {"$setOnInsert": {"expires_at": now + SEEN_TTL}},
            upsert=True,
        )
    except DuplicateKeyError:
        return False
    return res.upserted_id is not None


def _message_too_old(m: dict, now: datetime) -> bool:
    try:
        sent = datetime.fromtimestamp(int(m.get("timestamp")), tz=UTC)
    except (TypeError, ValueError):
        return False
    return now - sent > MAX_MESSAGE_AGE


async def process_message(db, settings: Settings, m: dict, name: str) -> None:
    message_id, wa_id = m.get("id"), m.get("from")
    if not message_id or not wa_id:
        return
    now = datetime.now(UTC)
    if not await _first_time(db, message_id, now):
        return  # Meta sent this one before
    if _message_too_old(m, now):
        logger.info("Skipping a WhatsApp message older than %s", MAX_MESSAGE_AGE)
        return

    inbound = parse_inbound(m, name)
    who = f"{name or 'Customer'} (+{wa_id})"

    lock = _lock_for(wa_id)
    try:
        async with lock:
            session = await db.wa_sessions.find_one({"_id": wa_id})
            result = handle(session, inbound, wa_id, owner_phone=await _owner_contact(db, settings), now=now)
            await db.wa_sessions.replace_one({"_id": wa_id}, result.session, upsert=True)

            for payload in result.messages:
                await client.send_message(settings, wa_id, payload)

            if result.lead:
                lead = result.lead
                phone = normalize_phone(f"+{wa_id}") or f"+{wa_id}"
                enquiry = Enquiry(
                    name=lead["name"],
                    phone=phone,
                    service=lead["service"],
                    message=lead["message"],
                    source="whatsapp",
                )
                await db.enquiries.insert_one(enquiry.to_mongo())
                await send_lead_notifications(enquiry.model_dump(), settings)

            if result.photo and m.get("type") == "image":
                media = await client.download_media(settings, (m.get("image") or {}).get("id", ""))
                if media:
                    await send_telegram_photo(media[0], media[1], f"📷 WhatsApp photo from {who}", settings)

            if result.forward:
                await send_telegram_text(f"💬 WhatsApp message from {who}:\n{result.forward}", settings)
    finally:
        _release_lock(wa_id)


async def pause_chat(db, wa_id: str) -> None:
    await db.wa_sessions.update_one(
        {"_id": wa_id},
        {"$set": {"paused_until": datetime.now(UTC) + ECHO_PAUSE}},
        upsert=True,
    )


async def process_webhook(payload: dict, db, settings: Settings) -> None:
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            field = change.get("field")
            try:
                if field == "smb_message_echoes":
                    # Owner replied from the WhatsApp Business app (coexistence): bot steps back.
                    for echo in value.get("message_echoes") or []:
                        if echo.get("to"):
                            await pause_chat(db, echo["to"])
                    continue
                if field != "messages":
                    continue
                if (value.get("metadata") or {}).get("phone_number_id") != settings.WA_PHONE_NUMBER_ID:
                    continue
                names = {
                    c.get("wa_id"): ((c.get("profile") or {}).get("name") or "") for c in value.get("contacts") or []
                }
                for m in value.get("messages") or []:
                    await process_message(db, settings, m, names.get(m.get("from"), ""))
            except Exception:
                logger.exception("WhatsApp webhook processing failed")


@whatsapp_router.get("/webhook")
async def verify_webhook(request: Request, settings: Settings = Depends(get_settings)):
    if not settings.WA_VERIFY_TOKEN:
        raise HTTPException(status_code=404, detail="Not Found")
    q = request.query_params
    token = q.get("hub.verify_token") or ""
    if q.get("hub.mode") == "subscribe" and hmac.compare_digest(token, settings.WA_VERIFY_TOKEN):
        return PlainTextResponse(q.get("hub.challenge") or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@whatsapp_router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    if not settings.whatsapp_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    raw = await request.body()
    if not valid_signature(raw, request.headers.get("x-hub-signature-256"), settings.WA_APP_SECRET):
        raise HTTPException(status_code=401, detail="Bad signature")
    try:
        payload = json.loads(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="Bad JSON") from None
    if payload.get("object") == "whatsapp_business_account":
        background_tasks.add_task(process_webhook, payload, db, settings)
    return {"ok": True}
