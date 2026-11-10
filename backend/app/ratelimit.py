import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from pymongo import ReturnDocument

logger = logging.getLogger("anweshan.ratelimit")


def parse_dt(val):
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=UTC)
            return dt
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


MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15
MAX_ENQUIRIES = 5
ENQUIRY_WINDOW_MINUTES = 10


async def register_failed_login(db, ip: str) -> None:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=LOCK_MINUTES)
    # Atomic increment, so parallel wrong guesses cannot overwrite each other's count.
    rec = await db.login_attempts.find_one_and_update(
        {"identifier": ip},
        {
            "$inc": {"count": 1},
            "$set": {"updated_at": now, "expires_at": expires},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if rec and rec.get("count", 0) >= MAX_FAILED_LOGINS:
        await db.login_attempts.update_one(
            {"_id": rec["_id"]},
            {"$set": {"locked_until": expires, "count": 0, "expires_at": expires}},
        )
        logger.warning("Admin login locked for %s minutes after repeated wrong passwords", LOCK_MINUTES)


async def clear_login_attempts(db, ip: str) -> None:
    await db.login_attempts.delete_many({"identifier": ip})


async def check_and_increment_enquiry_limit(db, ip: str) -> None:
    now = datetime.now(UTC)
    # End an old window here too, so the limit never becomes permanent if the
    # TTL index is missing or MongoDB's TTL cleanup runs late.
    await db.enquiry_rate_limits.delete_many({"ip": ip, "expires_at": {"$lte": now}})

    rec = await db.enquiry_rate_limits.find_one_and_update(
        {"ip": ip},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {
                "created_at": now,
                "expires_at": now + timedelta(minutes=ENQUIRY_WINDOW_MINUTES),
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    if rec and rec.get("count", 0) > MAX_ENQUIRIES:
        logger.warning("Enquiry rate limit exceeded")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please WhatsApp us instead.",
        )
