import pytest


@pytest.mark.anyio
async def test_admin_services_crud(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}

    # List services
    res = await authenticated_admin.get("/api/admin/services")
    assert res.status_code == 200
    initial_count = len(res.json())
    assert initial_count >= 3

    # Create service
    new_svc = {
        "title": "Turnkey Office Setup",
        "price": "₹3,00,000 onwards",
        "timeline": "60 days",
        "description": "Complete corporate interior work.",
        "active": True,
    }
    res_create = await authenticated_admin.post("/api/admin/services", json=new_svc, headers=headers)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["title"] == "Turnkey Office Setup"
    svc_id = created["id"]

    # Update service
    res_update = await authenticated_admin.put(
        f"/api/admin/services/{svc_id}",
        json={"price": "₹3,50,000 onwards"},
        headers=headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["price"] == "₹3,50,000 onwards"

    # Delete service
    res_delete = await authenticated_admin.delete(f"/api/admin/services/{svc_id}", headers=headers)
    assert res_delete.status_code == 200

    # 404 on deleting non-existent service
    res_404 = await authenticated_admin.delete(f"/api/admin/services/{svc_id}", headers=headers)
    assert res_404.status_code == 404

    # 404 on updating non-existent service
    res_up_404 = await authenticated_admin.put(
        f"/api/admin/services/{svc_id}",
        json={"price": "₹100"},
        headers=headers,
    )
    assert res_up_404.status_code == 404


@pytest.mark.anyio
async def test_admin_ideas_crud(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}

    # Create idea
    idea_data = {
        "title": "Minimalist Scandinavian Bedroom",
        "category": "homes",
        "description": "Light wood tones and sheer curtains.",
        "image": "https://example.com/photo.jpg",
    }
    res_create = await authenticated_admin.post("/api/admin/ideas", json=idea_data, headers=headers)
    assert res_create.status_code == 200
    created = res_create.json()
    idea_id = created["id"]

    # Update idea
    res_update = await authenticated_admin.put(
        f"/api/admin/ideas/{idea_id}",
        json={"title": "Updated Scandinavian Bedroom"},
        headers=headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["title"] == "Updated Scandinavian Bedroom"

    # Delete idea
    res_delete = await authenticated_admin.delete(f"/api/admin/ideas/{idea_id}", headers=headers)
    assert res_delete.status_code == 200

    # 404 on deleting non-existent idea
    res_del_404 = await authenticated_admin.delete(f"/api/admin/ideas/{idea_id}", headers=headers)
    assert res_del_404.status_code == 404


@pytest.mark.anyio
async def test_admin_enquiries_read_and_delete(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}

    # Create an enquiry
    res_enq = await authenticated_admin.post(
        "/api/enquiries",
        json={"name": "Admin Tester", "phone": "9876543210", "message": "Test"},
    )
    enq_id = res_enq.json()["id"]

    # List enquiries
    res_list = await authenticated_admin.get("/api/admin/enquiries")
    assert res_list.status_code == 200
    enquiries = res_list.json()
    assert any(e["id"] == enq_id for e in enquiries)

    # Mark as read
    res_read = await authenticated_admin.put(f"/api/admin/enquiries/{enq_id}/read", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["ok"] is True

    # Delete enquiry
    res_del = await authenticated_admin.delete(f"/api/admin/enquiries/{enq_id}", headers=headers)
    assert res_del.status_code == 200

    # 404 on deleting non-existent enquiry
    res_del_404 = await authenticated_admin.delete(f"/api/admin/enquiries/{enq_id}", headers=headers)
    assert res_del_404.status_code == 404


@pytest.mark.anyio
async def test_admin_settings_update(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}

    payload = {
        "phone": "+91 86584 29239",
        "whatsapp": "+91 86584 29239",
        "address": "Bhubaneswar, Odisha, India",
        "hours": "10:00 AM – 8:00 PM, Mon–Sat",
    }
    res = await authenticated_admin.put("/api/admin/settings", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["address"] == "Bhubaneswar, Odisha, India"
    assert data["hours"] == "10:00 AM – 8:00 PM, Mon–Sat"
