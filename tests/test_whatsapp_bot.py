import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta

import pytest

from app.whatsapp import flow
from app.whatsapp.flow import Inbound, handle
from app.whatsapp.texts import GREETING, LANGUAGE_BUTTONS, OPTIONS, T

WA = "919876543210"
NOW = datetime(2026, 11, 11, 10, 0, tzinfo=UTC)


def txt(s, name="Ravi Kumar"):
    return Inbound("text", text=s, name=name)


def tap(oid, name="Ravi Kumar"):
    return Inbound("choice", choice_id=oid, text="", name=name)


def run(steps, session=None, now=NOW):
    results = []
    for msg in steps:
        r = handle(session, msg, WA, owner_phone="+91 86584 29239", now=now)
        session = r.session
        results.append(r)
    return session, results


def body_of(payload):
    if payload["type"] == "text":
        return payload["text"]["body"]
    return payload["interactive"]["body"]["text"]


# ------------------------------------------------------------------ texts


def test_whatsapp_limits_respected():
    for _, title in LANGUAGE_BUTTONS:
        assert len(title) <= 20
    assert len(GREETING) <= 1024
    for key, options in OPTIONS.items():
        assert len(options) <= 10
        for _, titles in options:
            assert set(titles) == {"en", "hi", "or"}
            for t in titles.values():
                limit = 20 if key in ("status", "timeline", "photos", "photos_more") else 24
                assert len(t) <= limit, (key, t)
    for key, by_lang in T.items():
        assert set(by_lang) == {"en", "hi", "or"}, key
    for lang in ("en", "hi", "or"):
        assert len(T["choose"][lang]) <= 20


# ------------------------------------------------------------------ flow


def test_first_message_gets_greeting_and_language_buttons():
    session, [r] = run([txt("hi")])
    assert session["step"] == "lang"
    msg = r.messages[0]
    assert msg["interactive"]["type"] == "button"
    assert "ANWESHAN" in body_of(msg)
    ids = [b["reply"]["id"] for b in msg["interactive"]["action"]["buttons"]]
    assert ids == ["lang_en", "lang_hi", "lang_or"]


def test_full_home_path_english_creates_lead():
    session, results = run(
        [
            txt("Hello"),
            tap("lang_en"),
            tap("svc_home"),
            tap("size_2bhk"),
            txt("Patia, Bhubaneswar"),
            tap("status_new"),
            tap("budget_3"),
            tap("time_month"),
            Inbound("image", name="Ravi Kumar"),
            Inbound("image", name="Ravi Kumar"),
            tap("photos_done"),
            tap("visit_tmr_pm"),
        ]
    )
    assert session["status"] == "done"
    final = results[-1]
    assert final.lead is not None
    lead = final.lead
    assert lead["name"] == "Ravi Kumar"
    assert lead["service"] == "Full home interior"
    assert lead["source"] == "whatsapp"
    for part in ("Size: 2 BHK", "Area: Patia, Bhubaneswar", "Place: New place", "Budget: ₹2–5 lakh",
                 "Start: Within 1 month", "Photos: 2", "Visit / call: Tomorrow evening", "Language: English"):
        assert part in lead["message"]
    done_text = body_of(final.messages[0])
    assert "Thank you, Ravi Kumar" in done_text and "+91 86584 29239" in done_text
    # first photo gets "send more / Done", the second is silent, both forwarded
    assert results[8].messages and results[8].photo
    assert results[9].messages == [] and results[9].photo


def test_hindi_by_numbers_furniture_path():
    session, results = run(
        [txt("namaste"), txt("2"), txt("4"), txt("1 sofa aur 4 kursi"), txt("Cuttack"), txt("skip"), txt("4")]
    )
    assert session["lang"] == "hi"
    assert "कौन-सा फर्नीचर" in body_of(results[2].messages[0])
    lead = results[-1].lead
    assert lead["service"] == "Furniture repair"
    assert "Details: 1 sofa aur 4 kursi" in lead["message"]
    assert "Visit / call: Call me first" in lead["message"]
    assert "Language: Hindi" in lead["message"]
    assert "धन्यवाद" in body_of(results[-1].messages[0])


def test_odia_list_shows_numbered_options():
    _, results = run([txt("hi"), txt("3")])
    msg = results[1].messages[0]
    assert msg["interactive"]["type"] == "list"
    body = body_of(msg)
    assert "ଆପଣଙ୍କୁ କେଉଁ କାମରେ" in body and "1. ପୂରା ଘର ଇଣ୍ଟେରିଅର" in body
    assert msg["interactive"]["action"]["button"] == "ବାଛନ୍ତୁ"


def test_invalid_answer_reasks_same_question():
    session, results = run([txt("hi"), tap("lang_en"), txt("what is the price?")])
    assert session["step"] == "service"
    r = results[-1]
    assert body_of(r.messages[0]).startswith("Please choose one of the options")
    assert r.messages[1]["interactive"]["type"] == "list"


def test_unknown_language_reply_repeats_greeting():
    session, results = run([txt("hi"), txt("tamil")])
    assert session["step"] == "lang"
    assert "ANWESHAN" in body_of(results[-1].messages[0])


def test_too_short_location_is_rejected():
    session, results = run([txt("hi"), tap("lang_en"), tap("svc_kitchen"), tap("size_1bhk"), txt("ab")])
    assert session["step"] == "location"
    assert "more detail" in body_of(results[-1].messages[0])


def test_shared_location_is_accepted():
    session, _ = run([txt("hi"), tap("lang_en"), tap("svc_shop"), tap("size_shop"),
                      Inbound("location", text="https://maps.google.com/?q=20.3,85.8")])
    assert session["step"] == "status"
    assert session["answers"]["location"].startswith("https://maps.google.com")


def test_menu_restarts_and_keeps_language():
    session, _ = run([txt("hi"), tap("lang_hi"), tap("svc_home")])
    session, [r] = run([txt("MENU")], session)
    assert session["step"] == "lang" and session["answers"] == {}
    assert session["lang"] == "hi"


def test_stale_unfinished_chat_starts_over():
    session, _ = run([txt("hi"), tap("lang_en"), tap("svc_home")])
    session, [r] = run([tap("size_2bhk")], session, now=NOW + timedelta(hours=25))
    assert session["step"] == "lang"


def test_after_done_forwards_and_replies_once():
    session, _ = run([txt("hi"), tap("lang_en"), tap("svc_other"), txt("false ceiling only"),
                      txt("Puri"), tap("photos_skip"), tap("visit_weekend")])
    assert session["status"] == "done"
    later = NOW + timedelta(hours=13)
    session, [r1] = run([txt("what is the cost?")], session, now=later)
    assert r1.forward == "what is the cost?"
    assert r1.messages and "Our team has your details" in body_of(r1.messages[0])
    session, [r2] = run([txt("please call after 5")], session, now=later + timedelta(minutes=5))
    assert r2.forward == "please call after 5" and r2.messages == []
    assert r2.lead is None
    session, [r3] = run([txt("hi")], session, now=later + timedelta(minutes=6))
    assert session["step"] == "lang"


def test_paused_chat_is_silent():
    session = {"_id": WA, "paused_until": NOW + timedelta(hours=2)}
    _, [r] = run([txt("hi")], session)
    assert r.messages == [] and r.lead is None
    # once the pause is over, a pause-only record behaves like a new chat
    session2, [r2] = run([txt("hi")], session, now=NOW + timedelta(hours=3))
    assert session2["step"] == "lang" and r2.messages


def test_image_in_wrong_step_still_forwarded():
    _, results = run([txt("hi"), Inbound("image")])
    assert results[-1].photo is True


def test_lead_name_fallback():
    s = {"answers": {"service": "svc_home"}, "photos": 0, "lang": "en"}
    assert flow.build_lead(s, "", WA)["name"] == "WhatsApp customer"


# ------------------------------------------------------------------ webhook

SECRET = "test_app_secret_123"
VERIFY = "verify_me_please"
PHONE_ID = "1234567890"


@pytest.fixture
def wa_env(monkeypatch):
    monkeypatch.setenv("WA_VERIFY_TOKEN", VERIFY)
    monkeypatch.setenv("WA_APP_SECRET", SECRET)
    monkeypatch.setenv("WA_ACCESS_TOKEN", "token")
    monkeypatch.setenv("WA_PHONE_NUMBER_ID", PHONE_ID)
    from app.config import get_settings

    get_settings.cache_clear()

    sent, leads, photos, texts = [], [], [], []

    async def fake_send(settings, to, payload):
        sent.append((to, payload))
        return True

    async def fake_lead(enquiry, settings):
        leads.append(enquiry)

    async def fake_media(settings, media_id):
        return (b"img", "image/jpeg")

    async def fake_photo(data, mime, caption, settings):
        photos.append(caption)

    async def fake_text(text, settings):
        texts.append(text)

    import app.whatsapp.client as client
    import app.whatsapp.router as router

    monkeypatch.setattr(client, "send_message", fake_send)
    monkeypatch.setattr(client, "download_media", fake_media)
    monkeypatch.setattr(router, "send_lead_notifications", fake_lead)
    monkeypatch.setattr(router, "send_telegram_photo", fake_photo)
    monkeypatch.setattr(router, "send_telegram_text", fake_text)
    return {"sent": sent, "leads": leads, "photos": photos, "texts": texts}


_counter = {"n": 0}


def wa_payload(message: dict, phone_id=PHONE_ID):
    _counter["n"] += 1
    message = {"from": WA, "id": f"wamid.{_counter['n']}", "timestamp": str(int(time.time())), **message}
    return {
        "object": "whatsapp_business_account",
        "entry": [{"id": "x", "changes": [{"field": "messages", "value": {
            "messaging_product": "whatsapp",
            "metadata": {"display_phone_number": "91000", "phone_number_id": phone_id},
            "contacts": [{"profile": {"name": "Sita Das"}, "wa_id": WA}],
            "messages": [message],
        }}]}],
    }


async def post_signed(client, payload, secret=SECRET):
    raw = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return await client.post("/api/whatsapp/webhook", content=raw,
                             headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})


def t(body):
    return {"type": "text", "text": {"body": body}}


def b(oid):
    return {"type": "interactive", "interactive": {"type": "button_reply", "button_reply": {"id": oid, "title": oid}}}


def li(oid):
    return {"type": "interactive", "interactive": {"type": "list_reply", "list_reply": {"id": oid, "title": oid}}}


@pytest.mark.anyio
async def test_webhook_verify(app_client, wa_env):
    ok = await app_client.get("/api/whatsapp/webhook", params={
        "hub.mode": "subscribe", "hub.verify_token": VERIFY, "hub.challenge": "12345"})
    assert ok.status_code == 200 and ok.text == "12345"
    bad = await app_client.get("/api/whatsapp/webhook", params={
        "hub.mode": "subscribe", "hub.verify_token": "nope", "hub.challenge": "1"})
    assert bad.status_code == 403


@pytest.mark.anyio
async def test_webhook_disabled_without_settings(app_client):
    res = await app_client.get("/api/whatsapp/webhook", params={"hub.mode": "subscribe"})
    assert res.status_code == 404
    res = await app_client.post("/api/whatsapp/webhook", json={})
    assert res.status_code == 404


@pytest.mark.anyio
async def test_webhook_rejects_bad_signature(app_client, wa_env):
    res = await post_signed(app_client, wa_payload(t("hi")), secret="wrong")
    assert res.status_code == 401
    assert wa_env["sent"] == []


@pytest.mark.anyio
async def test_webhook_full_conversation_saves_enquiry(app_client, wa_env, authenticated_admin):
    steps = [t("hi"), b("lang_en"), li("svc_kitchen"), li("size_3bhk"), t("Nayapalli, Bhubaneswar"),
             b("status_old"), li("budget_2"), b("time_now"),
             {"type": "image", "image": {"id": "media1", "mime_type": "image/jpeg"}},
             b("photos_done"), li("visit_tmr_am")]
    for s in steps:
        res = await post_signed(app_client, wa_payload(s))
        assert res.status_code == 200

    assert all(to == WA for to, _ in wa_env["sent"])
    assert len(wa_env["leads"]) == 1
    lead = wa_env["leads"][0]
    assert lead["source"] == "whatsapp"
    assert lead["phone"] == "+91 98765 43210"
    assert wa_env["photos"] and "Sita Das" in wa_env["photos"][0]

    res = await authenticated_admin.get("/api/admin/enquiries")
    items = res.json()
    wa_items = [e for e in items if e.get("source") == "whatsapp"]
    assert len(wa_items) == 1
    assert wa_items[0]["service"] == "Kitchen & wardrobe"
    assert "Budget: ₹1–2 lakh" in wa_items[0]["message"]


@pytest.mark.anyio
async def test_webhook_duplicate_delivery_answered_once(app_client, wa_env):
    payload = wa_payload(t("hi"))
    await post_signed(app_client, payload)
    await post_signed(app_client, payload)
    assert len(wa_env["sent"]) == 1


@pytest.mark.anyio
async def test_webhook_other_phone_number_ignored(app_client, wa_env):
    await post_signed(app_client, wa_payload(t("hi"), phone_id="999"))
    assert wa_env["sent"] == []


@pytest.mark.anyio
async def test_webhook_old_message_ignored(app_client, wa_env):
    p = wa_payload(t("hi"))
    p["entry"][0]["changes"][0]["value"]["messages"][0]["timestamp"] = str(int(time.time()) - 8 * 3600)
    await post_signed(app_client, p)
    assert wa_env["sent"] == []


@pytest.mark.anyio
async def test_owner_echo_pauses_bot(app_client, wa_env):
    echo = {"object": "whatsapp_business_account", "entry": [{"id": "x", "changes": [{
        "field": "smb_message_echoes",
        "value": {"metadata": {"phone_number_id": PHONE_ID},
                  "message_echoes": [{"from": "91000", "to": WA, "id": "e1", "type": "text"}]}}]}]}
    await post_signed(app_client, echo)
    await post_signed(app_client, wa_payload(t("hi")))
    assert wa_env["sent"] == []


@pytest.mark.anyio
async def test_website_enquiry_still_marked_website(app_client):
    res = await app_client.post("/api/enquiries", json={"name": "Asha", "phone": "9876543210"})
    assert res.status_code == 200
    assert res.json()["source"] == "website"


# ------------------------------------------------------------------ website button (Ref: AI-...)


def test_direct_hi_still_asks_service():
    session, results = run([txt("Hi"), tap("lang_en")])
    assert session["step"] == "service"
    assert "prefill" not in session


def test_website_service_button_skips_service_question():
    msg = 'Hi Anweshan Infra! I am interested in "Modular Kitchen". Please tell me more.\n\nRef: AI-KITCHEN'
    session, results = run([txt(msg), tap("lang_hi")])
    assert session["answers"]["service"] == "svc_kitchen"
    assert session["step"] == "size"
    ack, question = results[-1].messages
    assert "किचन और वॉर्डरोब" in body_of(ack)
    assert question["interactive"]["type"] == "list"
    assert "जगह कितनी बड़ी" in body_of(question)


def test_website_furniture_tool_skips_service_and_details():
    msg = ("Hi Anweshan Infra! I used your Furniture Assessment tool.\nItem: Sofa\nNeed: Polish\n"
           "Please guide me.\n\nRef: AI-FURNITURE")
    session, results = run([txt(msg), txt("1")])
    assert session["step"] == "location"
    assert session["answers"]["details"] == "Item: Sofa, Need: Polish"
    session, results = run([txt("Balangir"), tap("photos_skip"), tap("visit_call")], session)
    lead = results[-1].lead
    assert lead["service"] == "Furniture repair"
    assert "(from website button)" in lead["message"]
    assert "Website message: Hi Anweshan Infra! I used your Furniture Assessment tool." in lead["message"]
    assert "Ref:" not in lead["message"]


def test_website_other_service_uses_card_title_as_details():
    msg = 'Hi Anweshan Infra! I am interested in "Bathroom renovation". Please tell me more.\n\nRef: AI-OTHER'
    session, _ = run([txt(msg), tap("lang_en")])
    assert session["step"] == "location"
    assert session["answers"]["details"] == "Interested in: Bathroom renovation"


def test_website_button_restarts_finished_or_running_chat():
    session, _ = run([txt("hi"), tap("lang_en"), tap("svc_home")])
    session, _ = run([txt("I loved your design\n\nRef: AI-SHOP"), tap("lang_en")], session)
    assert session["answers"] == {"service": "svc_shop"}
    assert session["step"] == "size"


def test_generic_website_button_without_ref_asks_service():
    session, _ = run([txt("Hi Anweshan Infra! I want to design my space. Please guide me."), tap("lang_en")])
    assert session["step"] == "service"
