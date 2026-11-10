"""Regression tests for the November 2026 bug audit fixes."""

import io
import time

import jwt
import pytest
from PIL import Image

ORIGIN = {"Origin": "http://localhost:3000"}


@pytest.mark.anyio
async def test_anonymous_logout_does_not_end_admin_session(authenticated_admin):
    from httpx import ASGITransport, AsyncClient
    from server import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as stranger:
        res = await stranger.post("/api/admin/logout")
        assert res.status_code == 200

    me = await authenticated_admin.get("/api/admin/me")
    assert me.status_code == 200


@pytest.mark.anyio
async def test_real_logout_still_ends_session(authenticated_admin):
    res = await authenticated_admin.post("/api/admin/logout", headers=ORIGIN)
    assert res.status_code == 200
    me = await authenticated_admin.get("/api/admin/me")
    assert me.status_code == 401


@pytest.mark.anyio
async def test_spoofed_forwarded_for_does_not_bypass_lockout(app_client):
    for i in range(5):
        res = await app_client.post(
            "/api/admin/login",
            json={"password": "wrong"},
            headers={**ORIGIN, "X-Forwarded-For": f"10.0.0.{i}"},
        )
        assert res.status_code == 401
    res = await app_client.post(
        "/api/admin/login",
        json={"password": "wrong"},
        headers={**ORIGIN, "X-Forwarded-For": "10.0.0.99"},
    )
    assert res.status_code == 429


@pytest.mark.anyio
async def test_signed_netlify_requests_use_visitor_ip(app_client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("NETLIFY_PROXY_SECRET", "test-proxy-secret-that-is-long-enough-123456")
    get_settings.cache_clear()
    sign = jwt.encode({"netlify_id": "x", "exp": int(time.time()) + 60}, "test-proxy-secret-that-is-long-enough-123456", algorithm="HS256")

    def visitor(n):
        return {"x-nf-sign": sign, "x-nf-client-connection-ip": f"203.0.113.{n}"}

    # Six different visitors behind the same proxy are not blocked by each other.
    for n in range(6):
        res = await app_client.post(
            "/api/enquiries", json={"name": "Ravi", "phone": "9876543210"}, headers=visitor(n)
        )
        assert res.status_code == 200, res.text

    # A forged signature is ignored (falls back to the connecting address).
    bad = {"x-nf-sign": "not-a-token", "x-nf-client-connection-ip": "198.51.100.1"}
    from app.security import get_client_ip

    class Req:
        headers = bad
        client = type("C", (), {"host": "127.0.0.1"})()

    assert get_client_ip(Req(), get_settings()) == "127.0.0.1"


@pytest.mark.anyio
async def test_enquiry_phone_is_normalised(app_client):
    res = await app_client.post("/api/enquiries", json={"name": "Ravi", "phone": "098765-43210"})
    assert res.status_code == 200
    assert res.json()["phone"] == "+91 98765 43210"

    res = await app_client.post("/api/enquiries", json={"name": "Ravi", "phone": "98765\n43210"})
    assert res.status_code == 400


@pytest.mark.anyio
async def test_invalid_enquiries_do_not_use_up_the_limit(app_client):
    for _ in range(6):
        res = await app_client.post("/api/enquiries", json={"name": "Ravi", "phone": "123"})
        assert res.status_code == 400
    res = await app_client.post("/api/enquiries", json={"name": "Ravi", "phone": "9876543210"})
    assert res.status_code == 200


@pytest.mark.anyio
async def test_settings_normalise_and_reject_empty_numbers(authenticated_admin):
    res = await authenticated_admin.put(
        "/api/admin/settings",
        json={"whatsapp": "86584 29239", "phone": "08658429239", "instagram": "@anweshaninfra"},
        headers=ORIGIN,
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["whatsapp"] == "+91 86584 29239"
    assert data["phone"] == "+91 86584 29239"
    assert data["instagram"] == "https://www.instagram.com/anweshaninfra"

    res = await authenticated_admin.put("/api/admin/settings", json={"whatsapp": ""}, headers=ORIGIN)
    assert res.status_code == 400


@pytest.mark.anyio
async def test_deleted_demo_content_is_not_seeded_again(authenticated_admin):
    from app.config import get_settings
    from app.db import get_db
    from app.security import hash_password
    from app.seed import seed_data

    services = (await authenticated_admin.get("/api/admin/services")).json()
    for s in services:
        await authenticated_admin.delete(f"/api/admin/services/{s['id']}", headers=ORIGIN)

    await seed_data(get_db(), get_settings(), hash_password)
    assert (await authenticated_admin.get("/api/admin/services")).json() == []


@pytest.mark.anyio
async def test_oversized_bodies_are_rejected_before_parsing(app_client):
    res = await app_client.post(
        "/api/enquiries",
        content=b"{" + b" " * (70 * 1024) + b"}",
        headers={"content-type": "application/json"},
    )
    assert res.status_code == 413

    res = await app_client.post(
        "/api/admin/upload",
        files={"file": ("big.jpg", b"0" * (10 * 1024 * 1024), "image/jpeg")},
        headers=ORIGIN,
    )
    assert res.status_code == 413


@pytest.mark.anyio
async def test_damaged_photo_gets_clear_error(authenticated_admin):
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), "white").save(buf, format="JPEG")
    truncated = buf.getvalue()[:600]
    res = await authenticated_admin.post(
        "/api/admin/upload", files={"file": ("cut.jpg", truncated, "image/jpeg")}, headers=ORIGIN
    )
    assert res.status_code == 400
    assert "damaged" in res.json()["detail"] or "Only JPG" in res.json()["detail"]


@pytest.mark.anyio
async def test_clearing_idea_photo_keeps_current_photo(authenticated_admin):
    ideas = (await authenticated_admin.get("/api/admin/ideas")).json()
    idea = ideas[0]
    res = await authenticated_admin.put(
        f"/api/admin/ideas/{idea['id']}", json={"title": "Renamed", "image": ""}, headers=ORIGIN
    )
    assert res.status_code == 200
    assert res.json()["image"] == idea["image"]
    assert res.json()["title"] == "Renamed"


@pytest.mark.anyio
async def test_datetime_created_at_does_not_break_gallery(app_client):
    from datetime import UTC, datetime

    from app.db import get_db

    await get_db().ideas.insert_one(
        {"id": "dt-1", "title": "Imported", "category": "homes", "image": "", "created_at": datetime.now(UTC)}
    )
    res = await app_client.get("/api/ideas")
    assert res.status_code == 200
    assert any(i["id"] == "dt-1" for i in res.json())


@pytest.mark.anyio
async def test_files_outside_upload_folders_are_not_served(app_client):
    res = await app_client.get("/api/files/secrets/config.json")
    assert res.status_code == 404
