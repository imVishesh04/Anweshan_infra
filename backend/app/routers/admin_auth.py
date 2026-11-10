import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.config import Settings, get_settings
from app.db import db_dependency
from app.models import LoginIn, PasswordChangeIn
from app.ratelimit import (
    check_login_lockout,
    clear_login_attempts,
    register_failed_login,
)
from app.security import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    hash_password,
    require_admin,
    set_auth_cookies,
    verify_csrf,
    verify_password,
)

logger = logging.getLogger("anweshan.admin_auth")

admin_auth_router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


@admin_auth_router.post("/login")
async def admin_login(
    body: LoginIn,
    request: Request,
    response: Response,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    ip = request.client.host if request.client else "unknown"
    verify_csrf(request, settings)
    await check_login_lockout(db, ip)

    pw_bytes = body.password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password cannot exceed 72 characters.")

    admin = await db.users.find_one({"role": "admin"})
    if not admin or not verify_password(body.password, admin.get("password_hash", "")):
        await register_failed_login(db, ip)
        raise HTTPException(status_code=401, detail="Wrong password. Please try again.")

    await clear_login_attempts(db, ip)
    token_version = admin.get("token_version", 1)

    access_token = create_access_token(admin.get("email"), token_version, settings.JWT_SECRET)
    refresh_token = create_refresh_token(admin.get("email"), token_version, settings.JWT_SECRET)

    set_auth_cookies(
        response,
        access_token,
        refresh_token,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"ok": True, "email": admin.get("email")}


@admin_auth_router.post("/refresh")
async def admin_refresh(
    request: Request,
    response: Response,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    admin = await db.users.find_one({"role": "admin"})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin user not found")

    token_ver = payload.get("ver")
    current_ver = admin.get("token_version", 1)
    if token_ver is None or token_ver != current_ver:
        raise HTTPException(status_code=401, detail="Session expired")

    access_token = create_access_token(admin.get("email"), current_ver, settings.JWT_SECRET)
    refresh_token = create_refresh_token(admin.get("email"), current_ver, settings.JWT_SECRET)

    set_auth_cookies(
        response,
        access_token,
        refresh_token,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"ok": True}


@admin_auth_router.post("/logout")
async def admin_logout(
    request: Request,
    response: Response,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    await db.users.update_one({"role": "admin"}, {"$inc": {"token_version": 1}})
    clear_auth_cookies(
        response,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"ok": True}


@admin_auth_router.get("/me")
async def admin_me(
    admin: dict = Depends(require_admin),
    settings: Settings = Depends(get_settings),
):
    return {"ok": True, "email": admin.get("email", settings.ADMIN_EMAIL)}


@admin_auth_router.put("/password")
async def admin_change_password(
    body: PasswordChangeIn,
    request: Request,
    response: Response,
    admin: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long.")

    pw_bytes = body.new_password.encode("utf-8")
    if len(pw_bytes) > 72:
        raise HTTPException(status_code=400, detail="Password cannot exceed 72 characters.")

    if not verify_password(body.current_password, admin.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    new_hash = hash_password(body.new_password)
    new_version = admin.get("token_version", 1) + 1

    await db.users.update_one(
        {"id": admin["id"]},
        {"$set": {"password_hash": new_hash, "token_version": new_version}},
    )

    # Re-issue cookies with new token version for current session
    access_token = create_access_token(admin.get("email"), new_version, settings.JWT_SECRET)
    refresh_token = create_refresh_token(admin.get("email"), new_version, settings.JWT_SECRET)

    set_auth_cookies(
        response,
        access_token,
        refresh_token,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    return {"ok": True}
