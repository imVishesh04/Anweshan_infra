import io

import pytest
from PIL import Image


def _create_test_image(format="PNG", size=(200, 200), color="blue") -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.mark.anyio
async def test_upload_valid_png_and_serve(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}
    png_data = _create_test_image("PNG")

    # Upload
    files = {"file": ("test_interior.png", png_data, "image/png")}
    res_upload = await authenticated_admin.post("/api/admin/upload", files=files, headers=headers)
    assert res_upload.status_code == 200
    data = res_upload.json()
    assert "path" in data
    assert "url" in data
    assert data["path"].startswith("uploads/")
    assert data["path"].endswith(".png")

    # Serve the uploaded file back
    storage_path = data["path"]
    res_serve = await authenticated_admin.get(f"/api/files/{storage_path}")
    assert res_serve.status_code == 200
    assert res_serve.headers["Content-Type"] == "image/png"
    assert "public, max-age=31536000, immutable" in res_serve.headers["Cache-Control"]
    assert res_serve.headers["X-Content-Type-Options"] == "nosniff"
    assert len(res_serve.content) > 0


@pytest.mark.anyio
async def test_upload_fake_image_rejected(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}
    fake_data = b"This is plain text, not a real JPEG image!"
    files = {"file": ("not_really_an_image.jpg", fake_data, "image/jpeg")}

    res = await authenticated_admin.post("/api/admin/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "Only JPG, PNG or WEBP photos are allowed." in res.json()["detail"]


@pytest.mark.anyio
async def test_upload_oversized_image_rejected(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}
    # 8 MB + 1 KB
    huge_data = b"X" * (8 * 1024 * 1024 + 1024)
    files = {"file": ("huge_photo.jpg", huge_data, "image/jpeg")}

    res = await authenticated_admin.post("/api/admin/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "Image must be smaller than 8 MB." in res.json()["detail"]


@pytest.mark.anyio
async def test_file_path_traversal_defense(app_client):
    res = await app_client.get("/api/files/../../etc/passwd")
    assert res.status_code == 404

    res_dot = await app_client.get("/api/files/....//secret.txt")
    assert res_dot.status_code == 404


@pytest.mark.anyio
async def test_serve_old_aurelia_path(authenticated_admin, temp_upload_dir):
    # Manually place an old file at aurelia-interiors/uploads/old_logo.jpg in storage
    old_rel_path = "aurelia-interiors/uploads/old_logo.jpg"
    target = temp_upload_dir / "aurelia-interiors" / "uploads" / "old_logo.jpg"
    target.parent.mkdir(parents=True, exist_ok=True)
    jpg_data = _create_test_image("JPEG")
    target.write_bytes(jpg_data)

    # Serving old path succeeds
    res = await authenticated_admin.get(f"/api/files/{old_rel_path}")
    assert res.status_code == 200
    assert res.headers["Content-Type"] == "image/jpeg"
    assert res.content == jpg_data

    # Missing old file returns 404
    res_missing = await authenticated_admin.get("/api/files/aurelia-interiors/uploads/non_existent.jpg")
    assert res_missing.status_code == 404


@pytest.mark.anyio
async def test_orphan_cleanup_on_idea_delete(authenticated_admin):
    headers = {"Origin": "http://localhost:3000"}
    png_data = _create_test_image("PNG")

    # 1. Upload photo
    files = {"file": ("orphan_test.png", png_data, "image/png")}
    res_upload = await authenticated_admin.post("/api/admin/upload", files=files, headers=headers)
    uploaded_path = res_upload.json()["path"]

    # 2. Create idea referencing uploaded image
    res_idea = await authenticated_admin.post(
        "/api/admin/ideas",
        json={"title": "Orphan Test Idea", "image": uploaded_path, "category": "homes"},
        headers=headers,
    )
    idea_id = res_idea.json()["id"]

    # File exists and can be served
    res_serve = await authenticated_admin.get(f"/api/files/{uploaded_path}")
    assert res_serve.status_code == 200

    # 3. Delete idea
    res_delete = await authenticated_admin.delete(f"/api/admin/ideas/{idea_id}", headers=headers)
    assert res_delete.status_code == 200

    # 4. Verify file was cleaned up from storage
    res_serve_after = await authenticated_admin.get(f"/api/files/{uploaded_path}")
    assert res_serve_after.status_code == 404
