import pytest


@pytest.mark.anyio
async def test_root(app_client):
    res = await app_client.get("/api/")
    assert res.status_code == 200
    assert res.json() == {"message": "ANWESHAN Infra API"}


@pytest.mark.anyio
async def test_health_and_ready(app_client):
    res_health = await app_client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "ok"}

    res_ready = await app_client.get("/api/ready")
    assert res_ready.status_code == 200
    assert res_ready.json() == {"status": "ready"}


@pytest.mark.anyio
async def test_site_settings(app_client):
    res = await app_client.get("/api/site")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "site"
    assert "phone" in data
    assert "whatsapp" in data
    assert "instagram" in data
    assert "_id" not in data


@pytest.mark.anyio
async def test_services_list(app_client):
    res = await app_client.get("/api/services")
    assert res.status_code == 200
    services = res.json()
    assert len(services) == 3
    for s in services:
        assert s["active"] is True
        assert "id" in s
        assert "_id" not in s


@pytest.mark.anyio
async def test_ideas_category_filtering(app_client):
    # Total ideas seeded: 7 (3 homes, 2 shops, 2 furniture)
    res_all = await app_client.get("/api/ideas")
    assert res_all.status_code == 200
    all_ideas = res_all.json()
    assert len(all_ideas) == 7

    # Homes filter
    res_homes = await app_client.get("/api/ideas?category=homes")
    assert res_homes.status_code == 200
    homes = res_homes.json()
    assert len(homes) == 3
    for idea in homes:
        assert idea["category"] == "homes"

    # Shops filter
    res_shops = await app_client.get("/api/ideas?category=shops")
    assert res_shops.status_code == 200
    shops = res_shops.json()
    assert len(shops) == 2
    for idea in shops:
        assert idea["category"] == "shops"

    # Furniture filter
    res_furniture = await app_client.get("/api/ideas?category=furniture")
    assert res_furniture.status_code == 200
    furniture = res_furniture.json()
    assert len(furniture) == 2
    for idea in furniture:
        assert idea["category"] == "furniture"

    # Unknown category falls back to all
    res_unknown = await app_client.get("/api/ideas?category=invalid")
    assert res_unknown.status_code == 200
    assert len(res_unknown.json()) == 7
