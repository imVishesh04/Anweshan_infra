import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response

from app.config import Settings, get_settings
from app.db import db_dependency

logger = logging.getLogger("anweshan.security")


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password cannot exceed 72 characters.")
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        pw_bytes = plain.encode("utf-8")
        if len(pw_bytes) > 72:
            return False
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(email: str, token_version: int, secret: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": email,
        "type": "access",
        "ver": token_version,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(email: str, token_version: int, secret: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": email,
        "type": "refresh",
        "ver": token_version,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=7),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    secure: bool = False,
    samesite: str = "lax",
) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=900,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=604800,
        path="/",
    )


def clear_auth_cookies(
    response: Response,
    secure: bool = False,
    samesite: str = "lax",
) -> None:
    response.delete_cookie(
        "access_token",
        path="/",
        secure=secure,
        samesite=samesite,
        httponly=True,
    )
    response.delete_cookie(
        "refresh_token",
        path="/",
        secure=secure,
        samesite=samesite,
        httponly=True,
    )


def verify_csrf(request: Request, settings: Settings) -> None:
    # Check Sec-Fetch-Site (modern browser defense against cross-site request forgery)
    sec_fetch_site = request.headers.get("sec-fetch-site", "").lower()
    if sec_fetch_site == "cross-site":
        logger.warning("CSRF blocked: Sec-Fetch-Site is cross-site")
        raise HTTPException(status_code=403, detail="Cross-site requests not allowed.")

    # Check Origin header if present
    origin = request.headers.get("origin")
    if origin:
        allowed = settings.cors_origins_list
        if origin not in allowed:
            logger.warning("CSRF blocked: Origin %s not in allowed %s", origin, allowed)
            raise HTTPException(status_code=403, detail="Origin not allowed.")


async def require_admin(
    request: Request,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    admin = await db.users.find_one({"role": "admin"})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin user not found")

    token_ver = payload.get("ver")
    current_ver = admin.get("token_version", 1)
    if token_ver is None or token_ver != current_ver:
        raise HTTPException(status_code=401, detail="Session expired")

    return admin
