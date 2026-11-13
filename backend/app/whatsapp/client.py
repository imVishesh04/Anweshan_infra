"""Small WhatsApp Cloud API client: send a message, download a photo.

Errors are logged with the status code and Meta's error code only, never the
access token or the customer's message text.
"""

import contextlib
import logging

import httpx

from app.config import Settings

logger = logging.getLogger("anweshan.whatsapp")

MAX_MEDIA_BYTES = 5 * 1024 * 1024  # Telegram photos are capped at 10 MB; 5 MB is plenty


def _graph(settings: Settings, path: str) -> str:
    return f"https://graph.facebook.com/{settings.WA_GRAPH_VERSION}/{path}"


def _headers(settings: Settings) -> dict:
    return {"Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}"}


async def send_message(settings: Settings, to: str, payload: dict) -> bool:
    body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to, **payload}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                _graph(settings, f"{settings.WA_PHONE_NUMBER_ID}/messages"),
                json=body,
                headers=_headers(settings),
            )
        if res.is_success:
            return True
        code = None
        with contextlib.suppress(ValueError):
            code = res.json().get("error", {}).get("code")
        logger.warning("WhatsApp send failed: HTTP %s, Meta error code %s", res.status_code, code)
    except Exception as exc:
        logger.error("WhatsApp send failed: %s", type(exc).__name__)
    return False


async def download_media(settings: Settings, media_id: str) -> tuple[bytes, str] | None:
    """Returns (bytes, mime type) for a photo the customer sent, or None."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            meta = await client.get(_graph(settings, media_id), headers=_headers(settings))
            if not meta.is_success:
                logger.warning("WhatsApp media lookup failed: HTTP %s", meta.status_code)
                return None
            info = meta.json()
            if int(info.get("file_size") or 0) > MAX_MEDIA_BYTES:
                logger.info("WhatsApp photo skipped: too big")
                return None
            res = await client.get(info["url"], headers=_headers(settings))
            if not res.is_success or len(res.content) > MAX_MEDIA_BYTES:
                return None
            return res.content, info.get("mime_type") or "image/jpeg"
    except Exception as exc:
        logger.error("WhatsApp media download failed: %s", type(exc).__name__)
        return None
