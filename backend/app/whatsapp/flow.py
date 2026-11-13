"""The WhatsApp bot conversation, as a pure state machine.

`handle()` takes the saved chat session and one incoming message and returns
what to save, what to send back, and (at the end) the finished lead.
It never talks to the network or the database, so it is easy to test.

Path for home / kitchen / shop work:
    language -> service -> size -> location -> new/old -> budget -> timeline -> photos -> visit -> done
Path for furniture repair / something else:
    language -> service -> details -> location -> photos -> visit -> done
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.whatsapp.texts import GREETING, LANGUAGE_BUTTONS, OPTIONS, SUMMARY_LABELS, T

SESSION_TIMEOUT = timedelta(hours=24)  # an unfinished chat starts over after this
AFTER_DONE_REPLY_GAP = timedelta(hours=12)  # don't repeat the "we'll call you" note too often
MAX_TEXT = 300

RESTART_WORDS = {"menu", "restart", "start", "start again", "मेनू", "ମେନୁ"}
GREETING_WORDS = {"hi", "hii", "hello", "hey", "namaste", "namaskar", "नमस्ते", "ନମସ୍କାର"}
SKIP_WORDS = {"skip", "no", "nahi", "na", "0", "छोड़ें", "ଛାଡ଼ନ୍ତୁ"}
DONE_WORDS = {"done", "ok", "okay", "ho gaya", "हो गया", "ହୋଇଗଲା"}

FURNITURE_LIKE = {"svc_furniture", "svc_other"}
LANG_NAMES = {"en": "English", "hi": "Hindi", "or": "Odia"}

# Website WhatsApp buttons end their pre-typed message with "Ref: AI-KITCHEN" etc.
# Then we already know the service and skip "What do you need help with?".
REF_RE = re.compile(r"\s*\bref:\s*ai-(home|kitchen|shop|furniture|other)\b\.?", re.IGNORECASE)
REF_TO_SERVICE = {
    "home": "svc_home",
    "kitchen": "svc_kitchen",
    "shop": "svc_shop",
    "furniture": "svc_furniture",
    "other": "svc_other",
}


def parse_website_ref(text: str) -> dict | None:
    """Reads the service (and any details) out of a website button's pre-typed message."""
    m = REF_RE.search(text or "")
    if not m:
        return None
    service = REF_TO_SERVICE[m.group(1).lower()]
    note = REF_RE.sub("", text).strip()
    prefill = {"service": service, "note": note[:300]}
    if service in FURNITURE_LIKE:
        # Furniture tool sends "Item: ..." and "Need: ..." lines; a service card sends "...in "<title>"".
        parts = [ln.strip() for ln in note.splitlines() if ln.strip().lower().startswith(("item:", "need:"))]
        if not parts:
            quoted = re.search(r'"([^"]{2,80})"', note)
            if quoted:
                parts = [f"Interested in: {quoted.group(1)}"]
        if parts:
            prefill["details"] = ", ".join(parts)[:MAX_TEXT]
    return prefill


@dataclass
class Inbound:
    """One customer message, already pulled out of Meta's webhook JSON."""

    kind: str  # "text" | "choice" | "image" | "location" | "other"
    text: str = ""
    choice_id: str | None = None  # id of a tapped button / list row
    name: str = ""  # the customer's WhatsApp profile name


@dataclass
class FlowResult:
    session: dict
    messages: list[dict] = field(default_factory=list)
    lead: dict | None = None
    forward: str | None = None  # text to pass on to the owner (Telegram)
    photo: bool = False  # the incoming image should be forwarded to the owner


# ---------------------------------------------------------------- payloads


def text_msg(body: str) -> dict:
    return {"type": "text", "text": {"body": body[:4096], "preview_url": False}}


def buttons_msg(body: str, buttons: list[tuple[str, str]]) -> dict:
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body[:1024]},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": bid, "title": title[:20]}} for bid, title in buttons[:3]]
            },
        },
    }


def list_msg(body: str, button_label: str, rows: list[tuple[str, str]]) -> dict:
    return {
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body[:1024]},
            "action": {
                "button": button_label[:20],
                "sections": [
                    {
                        "title": button_label[:24],
                        "rows": [{"id": rid, "title": title[:24]} for rid, title in rows[:10]],
                    }
                ],
            },
        },
    }


# ---------------------------------------------------------------- helpers


def _now() -> datetime:
    return datetime.now(UTC)


def _as_dt(value) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split()).strip(".!")


def _options(key: str, lang: str) -> list[tuple[str, str]]:
    return [(oid, titles[lang]) for oid, titles in OPTIONS[key]]


def _title(key: str, oid: str, lang: str) -> str:
    for option_id, titles in OPTIONS[key]:
        if option_id == oid:
            return titles[lang]
    return oid


def _numbered(body: str, rows: list[tuple[str, str]]) -> str:
    lines = "\n".join(f"{i}. {title}" for i, (_, title) in enumerate(rows, start=1))
    return f"{body}\n\n{lines}"


def _match_option(key: str, msg: Inbound) -> str | None:
    """Accept a tap, the option number ("2"), or the option text in any language."""
    ids = [oid for oid, _ in OPTIONS[key]]
    if msg.choice_id in ids:
        return msg.choice_id
    if msg.kind != "text":
        return None
    typed = _norm(msg.text)
    if typed.isdigit() and 1 <= int(typed) <= len(ids):
        return ids[int(typed) - 1]
    for oid, titles in OPTIONS[key]:
        if typed in {_norm(t) for t in titles.values()}:
            return oid
    return None


def _match_language(msg: Inbound) -> str | None:
    if msg.choice_id in {"lang_en", "lang_hi", "lang_or"}:
        return msg.choice_id.removeprefix("lang_")
    typed = _norm(msg.text)
    table = {
        "1": "en",
        "english": "en",
        "eng": "en",
        "2": "hi",
        "hindi": "hi",
        "हिंदी": "hi",
        "हिन्दी": "hi",
        "3": "or",
        "odia": "or",
        "oriya": "or",
        "ଓଡ଼ିଆ": "or",
        "ଓଡିଆ": "or",
    }
    return table.get(typed)


def _question(step: str, lang: str, session: dict) -> list[dict]:
    """The message(s) that ask the question for `step`."""
    if step == "lang":
        return [buttons_msg(GREETING, LANGUAGE_BUTTONS)]
    if step in ("service", "size", "budget", "visit"):
        prompt = {"service": "ask_service", "size": "ask_size", "budget": "ask_budget", "visit": "ask_visit"}[step]
        rows = _options(step, lang)
        return [list_msg(_numbered(T[prompt][lang], rows), T["choose"][lang], rows)]
    if step in ("status", "timeline"):
        prompt = {"status": "ask_status", "timeline": "ask_timeline"}[step]
        rows = _options(step, lang)
        return [buttons_msg(_numbered(T[prompt][lang], rows), rows)]
    if step == "details":
        key = "ask_furniture" if session.get("answers", {}).get("service") == "svc_furniture" else "ask_other"
        return [text_msg(T[key][lang])]
    if step == "location":
        return [text_msg(T["ask_location"][lang])]
    if step == "photos":
        key = "photos_more" if session.get("photos") else "photos"
        prompt = "photo_received" if session.get("photos") else "ask_photos"
        return [buttons_msg(T[prompt][lang], _options(key, lang))]
    raise ValueError(f"unknown step {step}")


def _new_session(wa_id: str, now: datetime) -> dict:
    return {
        "_id": wa_id,
        "step": "lang",
        "lang": "en",
        "answers": {},
        "photos": 0,
        "status": "active",
        "started_at": now,
        "updated_at": now,
    }


def _next_after(step: str, session: dict) -> str:
    furniture_path = session["answers"].get("service") in FURNITURE_LIKE
    if furniture_path:
        order = ["service", "details", "location", "photos", "visit", "done"]
    else:
        order = ["service", "size", "location", "status", "budget", "timeline", "photos", "visit", "done"]
    return order[order.index(step) + 1]


def _contact_line(lang: str, owner_phone: str | None) -> str:
    return T["contact_line"][lang].format(phone=owner_phone) if owner_phone else ""


# ---------------------------------------------------------------- summary / lead


_SUMMARY_ORDER = [
    ("service", "service"),
    ("details", None),
    ("size", "size"),
    ("location", None),
    ("status", "status"),
    ("budget", "budget"),
    ("timeline", "timeline"),
    ("visit", "visit"),
]


def _summary_lines(session: dict, lang: str) -> list[str]:
    answers = session["answers"]
    lines = []
    for key, option_key in _SUMMARY_ORDER:
        if key not in answers:
            continue
        value = _title(option_key, answers[key], lang) if option_key else answers[key]
        lines.append(f"{SUMMARY_LABELS[key][lang]}: {value}")
    if session.get("photos"):
        lines.append(f"{SUMMARY_LABELS['photos'][lang]}: {session['photos']}")
    return lines


def build_lead(session: dict, profile_name: str, wa_id: str) -> dict:
    """The enquiry saved for the admin panel. Always in English so the owner can read it."""
    answers = session["answers"]
    lines = _summary_lines(session, "en")[1:]  # service has its own field
    if session.get("photos"):
        lines[-1] = f"Photos: {session['photos']} (sent to Telegram)"
    lines.append(f"Language: {LANG_NAMES.get(session.get('lang', 'en'), 'English')}")
    header = "WhatsApp bot enquiry"
    prefill = session.get("prefill")
    if prefill:
        header += " (from website button)"
        if prefill.get("note"):
            lines.append(f"Website message: {prefill['note']}")
    name = " ".join((profile_name or "").split())[:80]
    return {
        "name": name if len(name) >= 2 else "WhatsApp customer",
        "wa_id": wa_id,
        "service": _title("service", answers.get("service", ""), "en")[:100],
        "message": (header + "\n" + "\n".join(lines))[:1000],
        "source": "whatsapp",
    }


# ---------------------------------------------------------------- main entry


def handle(
    session: dict | None,
    msg: Inbound,
    wa_id: str,
    *,
    owner_phone: str | None = None,
    now: datetime | None = None,
) -> FlowResult:
    now = now or _now()

    # The owner is chatting by hand (WhatsApp Business app on the same number): stay out of it.
    paused_until = _as_dt((session or {}).get("paused_until"))
    if session and paused_until and paused_until > now:
        return FlowResult(session=session)

    if session is not None and "step" not in session:
        session = None  # only a pause marker was saved, no real chat yet

    result = _handle(session, msg, wa_id, owner_phone, now)
    if msg.kind == "image":
        result.photo = True  # never lose a customer's photo, whatever step it came in
    return result


def _handle(session: dict | None, msg: Inbound, wa_id: str, owner_phone: str | None, now: datetime) -> FlowResult:
    typed = _norm(msg.text) if msg.kind == "text" else ""

    updated = _as_dt((session or {}).get("updated_at"))
    stale = (
        session is not None
        and session.get("status") == "active"
        and (updated is None or now - updated > SESSION_TIMEOUT)
    )

    prefill = parse_website_ref(msg.text) if msg.kind == "text" else None

    # Start (or start over). A message from a website button always starts a fresh enquiry.
    if (
        session is None
        or stale
        or prefill
        or typed in RESTART_WORDS
        or (session.get("status") == "done" and typed in GREETING_WORDS)
    ):
        new = _new_session(wa_id, now)
        if prefill:
            new["prefill"] = prefill
        if session and session.get("lang") and typed in RESTART_WORDS:
            new["lang"] = session["lang"]
        return FlowResult(session=new, messages=_question("lang", new["lang"], new))

    session = {**session, "answers": dict(session.get("answers") or {})}
    lang = session.get("lang", "en")

    # Finished chats: pass anything new on to the owner, reply politely now and then.
    if session.get("status") == "done":
        result = FlowResult(session=session)
        if msg.kind in ("text", "location") and msg.text:
            result.forward = msg.text[:1000]
        last = _as_dt(session.get("after_done_reply_at"))
        if last is None or now - last > AFTER_DONE_REPLY_GAP:
            result.messages = [text_msg(T["after_done"][lang].format(contact=_contact_line(lang, owner_phone)))]
            session["after_done_reply_at"] = now
        return result

    step = session["step"]
    session["updated_at"] = now

    def reask(extra: str = "invalid") -> FlowResult:
        return FlowResult(session=session, messages=[text_msg(T[extra][lang]), *_question(step, lang, session)])

    def advance(current: str) -> FlowResult:
        nxt = _next_after(current, session)
        session["step"] = nxt
        if nxt == "done":
            return _finish(session, msg, wa_id, owner_phone, now)
        return FlowResult(session=session, messages=_question(nxt, lang, session))

    if step == "lang":
        chosen = _match_language(msg)
        if not chosen:
            return FlowResult(session=session, messages=_question("lang", lang, session))
        session["lang"] = lang = chosen
        prefill = session.get("prefill")
        if not prefill:
            session["step"] = "service"
            return FlowResult(session=session, messages=_question("service", lang, session))
        # Came from a website button: service is known, go straight to the next question.
        session["answers"]["service"] = prefill["service"]
        nxt = _next_after("service", session)
        if nxt == "details" and prefill.get("details"):
            session["answers"]["details"] = prefill["details"]
            nxt = _next_after("details", session)
        session["step"] = nxt
        ack = text_msg(T["got_service"][lang].format(service=_title("service", prefill["service"], lang)))
        return FlowResult(session=session, messages=[ack, *_question(nxt, lang, session)])

    if step in ("service", "size", "status", "budget", "timeline", "visit"):
        chosen = _match_option(step, msg)
        if not chosen:
            return reask()
        session["answers"][step] = chosen
        return advance(step)

    if step in ("details", "location"):
        if msg.kind == "location" and step == "location" and msg.text:
            value = msg.text
        elif msg.kind == "text":
            value = " ".join(msg.text.split())
        else:
            return reask()
        if len(value) < 3:
            return reask("too_short")
        session["answers"][step] = value[:MAX_TEXT]
        return advance(step)

    if step == "photos":
        if msg.kind == "image":
            session["photos"] = int(session.get("photos") or 0) + 1
            # Ask "send more or Done?" only after the first photo, not after every one.
            messages = _question("photos", lang, session) if session["photos"] == 1 else []
            return FlowResult(session=session, messages=messages, photo=True)
        if msg.choice_id in ("photos_skip", "photos_done") or typed in SKIP_WORDS | DONE_WORDS:
            return advance("photos")
        return reask()

    # Unknown step (old data): start over.
    new = _new_session(wa_id, now)
    return FlowResult(session=new, messages=_question("lang", "en", new))


def _finish(session: dict, msg: Inbound, wa_id: str, owner_phone: str | None, now: datetime) -> FlowResult:
    lang = session.get("lang", "en")
    session["status"] = "done"
    session["step"] = "done"
    session["finished_at"] = now
    session["after_done_reply_at"] = now
    first_name = " ".join((msg.name or "").split())[:30] or T["customer"][lang]
    body = T["done"][lang].format(
        name=first_name,
        summary="\n".join(_summary_lines(session, lang)),
        contact=_contact_line(lang, owner_phone),
    )
    return FlowResult(session=session, messages=[text_msg(body)], lead=build_lead(session, msg.name, wa_id))
