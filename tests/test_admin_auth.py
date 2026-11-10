import pytest


@pytest.mark.anyio
async def test_admin_login_wrong_password(app_client):
    res = await app_client.post(
        "/api/admin/login",
        json={"password": "wrong_password"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res.status_code == 401
    assert "Wrong password. Please try again." in res.json()["detail"]


@pytest.mark.anyio
async def test_admin_login_brute_force_lockout(app_client):
    # 4 wrong attempts
    for _ in range(4):
        res = await app_client.post(
            "/api/admin/login",
            json={"password": "wrong_password"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert res.status_code == 401

    # 5th wrong attempt triggers lockout
    res_fifth = await app_client.post(
        "/api/admin/login",
        json={"password": "wrong_password"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_fifth.status_code == 401

    # 6th attempt is blocked with 429
    res_locked = await app_client.post(
        "/api/admin/login",
        json={"password": "test_admin_password_123"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_locked.status_code == 429
    assert "Too many wrong attempts. Please try again in 15 minutes." in res_locked.json()["detail"]


@pytest.mark.anyio
async def test_admin_login_success_and_cookies(app_client):
    res = await app_client.post(
        "/api/admin/login",
        json={"password": "test_admin_password_123"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies


@pytest.mark.anyio
async def test_admin_me_endpoint(app_client):
    # Without cookie -> 401
    res_unauth = await app_client.get("/api/admin/me")
    assert res_unauth.status_code == 401

    # Login to set cookies
    res_login = await app_client.post(
        "/api/admin/login",
        json={"password": "test_admin_password_123"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_login.status_code == 200

    # With cookie -> 200
    res_auth = await app_client.get("/api/admin/me")
    assert res_auth.status_code == 200
    assert res_auth.json()["ok"] is True
    assert "email" in res_auth.json()


@pytest.mark.anyio
async def test_admin_refresh_token(authenticated_admin):
    res_refresh = await authenticated_admin.post(
        "/api/admin/refresh",
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_refresh.status_code == 200
    assert res_refresh.json()["ok"] is True
    assert "access_token" in res_refresh.cookies


@pytest.mark.anyio
async def test_admin_logout_revokes_token(authenticated_admin):
    # Save the current access token
    token = authenticated_admin.cookies.get("access_token")

    # Logout
    res_logout = await authenticated_admin.post(
        "/api/admin/logout",
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_logout.status_code == 200

    # Try to access /api/admin/me with old access token in Authorization header
    res_me = await authenticated_admin.get(
        "/api/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_me.status_code == 401
    assert "Session expired" in res_me.json()["detail"]


@pytest.mark.anyio
async def test_admin_change_password(authenticated_admin):
    # Change password
    res = await authenticated_admin.put(
        "/api/admin/password",
        json={
            "current_password": "test_admin_password_123",
            "new_password": "brand_new_admin_password_456",
        },
        headers={"Origin": "http://localhost:3000"},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True

    # Old password no longer works
    res_old = await authenticated_admin.post(
        "/api/admin/login",
        json={"password": "test_admin_password_123"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_old.status_code == 401

    # New password works
    res_new = await authenticated_admin.post(
        "/api/admin/login",
        json={"password": "brand_new_admin_password_456"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert res_new.status_code == 200


@pytest.mark.anyio
async def test_csrf_origin_rejection(authenticated_admin):
    # Bad Origin header rejected on state-changing request
    res_bad_origin = await authenticated_admin.post(
        "/api/admin/services",
        json={"title": "Test Service"},
        headers={"Origin": "http://malicious-attacker.com"},
    )
    assert res_bad_origin.status_code == 403
    assert "Origin not allowed." in res_bad_origin.json()["detail"]

    # Sec-Fetch-Site cross-site rejected
    res_cross_site = await authenticated_admin.post(
        "/api/admin/services",
        json={"title": "Test Service"},
        headers={
            "Origin": "http://localhost:3000",
            "Sec-Fetch-Site": "cross-site",
        },
    )
    assert res_cross_site.status_code == 403
    assert "Cross-site requests not allowed." in res_cross_site.json()["detail"]
