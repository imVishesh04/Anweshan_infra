import pytest


@pytest.mark.anyio
async def test_create_valid_enquiry(app_client):
    payload = {
        "name": "Priya Sharma",
        "phone": "+91 98765 43210",
        "service": "Full Home Interiors",
        "message": "Looking for 3BHK interior design in Bhubaneswar.",
    }
    res = await app_client.post("/api/enquiries", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Priya Sharma"
    assert data["phone"] == "+91 98765 43210"
    assert data["service"] == "Full Home Interiors"
    assert data["read"] is False
    assert "id" in data
    assert "_id" not in data


@pytest.mark.anyio
async def test_enquiry_validation_errors(app_client):
    # Short name
    res = await app_client.post("/api/enquiries", json={"name": "A", "phone": "9876543210"})
    assert res.status_code == 400
    assert "Please enter your name." in res.json()["detail"]

    # Invalid phone (letters or too short)
    res = await app_client.post("/api/enquiries", json={"name": "Valid Name", "phone": "12345"})
    assert res.status_code == 400
    assert "Please enter a valid phone number." in res.json()["detail"]

    res = await app_client.post("/api/enquiries", json={"name": "Valid Name", "phone": "not-a-number"})
    assert res.status_code == 400
    assert "Please enter a valid phone number." in res.json()["detail"]


@pytest.mark.anyio
async def test_enquiry_rate_limiting(app_client):
    payload = {
        "name": "Rate Limit Tester",
        "phone": "9876543210",
        "service": "Shop Interiors",
        "message": "Testing limits",
    }
    # First 5 succeed
    for i in range(5):
        res = await app_client.post("/api/enquiries", json=payload)
        assert res.status_code == 200, f"Attempt {i+1} failed"

    # 6th attempt is blocked with 429
    res_blocked = await app_client.post("/api/enquiries", json=payload)
    assert res_blocked.status_code == 429
    assert "Too many requests. Please WhatsApp us instead." in res_blocked.json()["detail"]
