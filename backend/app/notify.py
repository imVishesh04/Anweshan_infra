import logging

import anyio
import httpx

from app.config import Settings

logger = logging.getLogger("anweshan.notify")


def _send_twilio_whatsapp(
    sid: str,
    token: str,
    from_num: str,
    to_num: str,
    body: str,
) -> None:
    try:
        from twilio.rest import Client

        to_formatted = to_num if to_num.startswith("whatsapp:") else f"whatsapp:{to_num}"
        from_formatted = from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}"

        client = Client(sid, token)
        msg = client.messages.create(
            from_=from_formatted,
            to=to_formatted,
            body=body,
        )
        logger.info("Twilio WhatsApp notification sent: %s", msg.sid)
    except Exception as exc:
        logger.error("Twilio WhatsApp notification failed: %s", exc)


async def send_lead_notifications(enquiry_dict: dict, settings: Settings) -> None:
    name = enquiry_dict.get("name", "Unknown")
    phone = enquiry_dict.get("phone", "Unknown")
    service = enquiry_dict.get("service") or "Not chosen"
    message = enquiry_dict.get("message") or "-"

    body = (
        "New Enquiry — ANWESHAN Infra\n"
        f"Name: {name}\n"
        f"Phone: {phone}\n"
        f"Service: {service}\n"
        f"Message: {message}\n"
        "Open your website admin to reply."
    )

    notified = False

    # 1. Telegram alert
    if settings.NOTIFY_TELEGRAM_BOT_TOKEN and settings.NOTIFY_TELEGRAM_CHAT_ID:
        notified = True
        try:
            tg_url = f"https://api.telegram.org/bot{settings.NOTIFY_TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    tg_url,
                    json={
                        "chat_id": settings.NOTIFY_TELEGRAM_CHAT_ID,
                        "text": body,
                    },
                )
                if res.is_success:
                    logger.info("Telegram lead notification sent successfully.")
                else:
                    logger.warning("Telegram notification responded with status %s", res.status_code)
        except Exception as exc:
            # Never log the exception text: httpx errors include the URL, which holds the bot token.
            logger.error("Telegram notification failed: %s", type(exc).__name__)

    # 2. Resend email alert
    if settings.RESEND_API_KEY and settings.NOTIFY_EMAIL_TO:
        notified = True
        try:
            resend_url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "from": settings.NOTIFY_EMAIL_FROM,
                "to": [settings.NOTIFY_EMAIL_TO],
                "subject": f"New Lead from {' '.join(name.split())[:60]} — ANWESHAN Infra",
                "text": body,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(resend_url, json=payload, headers=headers)
                if res.is_success:
                    logger.info("Resend email lead notification sent successfully.")
                else:
                    logger.warning("Resend notification responded with status %s: %s", res.status_code, res.text)
        except Exception as exc:
            logger.error("Resend email notification failed: %s", exc)

    # 3. Twilio WhatsApp alert
    if (
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_WHATSAPP_FROM
        and settings.OWNER_WHATSAPP
    ):
        notified = True
        try:
            await anyio.to_thread.run_sync(
                _send_twilio_whatsapp,
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_WHATSAPP_FROM,
                settings.OWNER_WHATSAPP,
                body,
            )
        except Exception as exc:
            logger.error("Twilio WhatsApp task failed: %s", exc)

    if not notified:
        logger.info("No lead notifier configured - skipping lead alert")
