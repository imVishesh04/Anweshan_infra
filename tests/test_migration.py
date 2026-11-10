import json
import shutil
import tempfile
from pathlib import Path

import pytest
from app.config import get_settings
from PIL import Image
from pymongo import AsyncMongoClient
from scripts.import_emergent_export import import_export


@pytest.fixture
def mock_export_folder():
    d = Path(tempfile.mkdtemp(prefix="mock_emergent_export_"))

    # Services
    services_data = [
        {"id": "svc-1", "title": "Custom Woodwork", "price": "₹50,000", "active": True, "sort_order": 1},
        {"id": "svc-2", "title": "False Ceiling", "price": "₹80,000", "active": True, "sort_order": 2},
    ]
    (d / "services.json").write_text(json.dumps(services_data), encoding="utf-8")

    # Ideas
    ideas_data = [
        {"id": "idea-1", "title": "Sample Arch", "category": "homes", "image": "uploads/sample_arch.jpg"},
        {"id": "idea-2", "title": "External Photo", "category": "shops", "image": "https://example.com/shop.jpg"},
    ]
    (d / "ideas.json").write_text(json.dumps(ideas_data), encoding="utf-8")

    # Enquiries
    enquiries_data = [
        {"id": "enq-1", "name": "Rahul Verma", "phone": "9876543210", "message": "Imported lead", "read": False},
    ]
    (d / "enquiries.json").write_text(json.dumps(enquiries_data), encoding="utf-8")

    # Settings
    settings_data = {
        "id": "site",
        "phone": "+91 86584 29239",
        "whatsapp": "+91 86584 29239",
        "address": "Bhubaneswar",
    }
    (d / "settings.json").write_text(json.dumps(settings_data), encoding="utf-8")

    # Files
    files_data = [
        {"id": "file-1", "storage_path": "uploads/sample_arch.jpg", "content_type": "image/jpeg", "size": 1024, "is_deleted": False},
    ]
    (d / "files.json").write_text(json.dumps(files_data), encoding="utf-8")

    # Image file under images/uploads/sample_arch.jpg
    img_dir = d / "images" / "uploads"
    img_dir.mkdir(parents=True, exist_ok=True)
    img_file = img_dir / "sample_arch.jpg"
    test_img = Image.new("RGB", (100, 100), color="green")
    test_img.save(img_file, format="JPEG")

    yield d

    shutil.rmtree(d, ignore_errors=True)


@pytest.mark.anyio
async def test_import_emergent_export_idempotent(app_client, mock_export_folder):
    settings = get_settings()
    client = AsyncMongoClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]

    initial_users_count = await db.users.count_documents({})

    # 1. First import run
    await import_export(mock_export_folder)

    assert await db.services.count_documents({"id": "svc-1"}) == 1
    assert await db.services.count_documents({"id": "svc-2"}) == 1
    assert await db.ideas.count_documents({"id": "idea-1"}) == 1
    assert await db.enquiries.count_documents({"id": "enq-1"}) == 1

    site_doc = await db.settings.find_one({"id": "site"})
    assert site_doc["address"] == "Bhubaneswar"

    # Verify image can be served
    res_img = await app_client.get("/api/files/uploads/sample_arch.jpg")
    assert res_img.status_code == 200

    # 2. Second import run (must be idempotent - no duplicate records)
    await import_export(mock_export_folder)

    assert await db.services.count_documents({"id": "svc-1"}) == 1
    assert await db.services.count_documents({"id": "svc-2"}) == 1
    assert await db.ideas.count_documents({"id": "idea-1"}) == 1
    assert await db.enquiries.count_documents({"id": "enq-1"}) == 1

    # Verify users collection was never modified
    final_users_count = await db.users.count_documents({})
    assert final_users_count == initial_users_count

    await client.close()
