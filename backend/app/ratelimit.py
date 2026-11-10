import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from pymongo import ReturnDocument

logger = logging.getLogger("anweshan.ratelimit")


def parse_dt(val):
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return None
    return None


async def check_login_lockout(db, ip: str) -> None:
    rec = await db.login_attempts.find_one({"identifier": ip})
    if not rec:
        return
    locked_until = parse_dt(rec.get("locked_until"))
    if locked_until and datetime.now(UTC) < locked_until:
        raise HTTPException(
            status_code=429,
            detail="Too many wrong attempts. Please try again in 15 minutes.",
        )


async def register_failed_login(db, ip: str) -> None:
    now = datetime.now(UTC)
    rec = await db.login_attempts.find_one({"identifier": ip})
    current_count = (rec or {}).get("count", 0)
    new_count = current_count + 1

    update = {
        "count": new_count,
        "updated_at": now,
        "expires_at": now + timedelta(minutes=15),
    }
    if new_count >= 5:
        update["locked_until"] = now + timedelta(minutes=15)
        update["count"] = 0

    await db.login_attempts.update_one(
        {"identifier": ip},
        {
            "$set": update,
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


async def clear_login_attempts(db, ip: str) -> None:
    await db.login_attempts.delete_one({"identifier": ip})


async def check_and_increment_enquiry_limit(db, ip: str) -> None:
    now = datetime.now(UTC)
    window_expiry = now + timedelta(minutes=10)

    # Atomic find_one_and_update
    rec = await db.enquiry_rate_limits.find_one_and_update(
        {"ip": ip},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {"created_at": now, "expires_at": window_expiry},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    if rec and rec.get("count", 0) > 5:
        logger.warning("Enquiry rate limit exceeded for IP %s", ip)
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please WhatsApp us instead.",
        )
