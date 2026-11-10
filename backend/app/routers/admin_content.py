import contextlib
import io
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from PIL import Image, ImageOps
from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.config import Settings, get_settings
from app.db import db_dependency
from app.models import (
    DesignIdea,
    Enquiry,
    IdeaIn,
    Service,
    ServiceIn,
    SettingsIn,
    SiteSettings,
)
from app.security import require_admin, verify_csrf
from app.storage import get_storage

logger = logging.getLogger("anweshan.admin_content")

admin_content_router = APIRouter(prefix="/api/admin", tags=["admin-content"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
Image.MAX_IMAGE_PIXELS = 25_000_000  # Sane decompression bomb limit


async def _cleanup_uploaded_image(image_path: str | None, db, storage) -> None:
    if not image_path or image_path.startswith("http"):
        return
    file_doc = await db.files.find_one({"storage_path": image_path, "is_deleted": False})
    if file_doc:
        await db.files.update_one({"storage_path": image_path}, {"$set": {"is_deleted": True}})
        await storage.delete(image_path)
        logger.info("Cleaned up orphaned uploaded file: %s", image_path)


# --- Services CRUD ---
@admin_content_router.get("/services")
async def admin_services(_: dict = Depends(require_admin), db=Depends(db_dependency)):
    docs = await db.services.find({}, {"_id": 0}).sort([("sort_order", ASCENDING)]).to_list(100)
    return [Service.from_mongo(d).model_dump() for d in docs]


@admin_content_router.post("/services", response_model=Service)
async def admin_create_service(
    input: ServiceIn,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    data = input.model_dump(exclude_unset=True)
    if not (data.get("title") or "").strip():
        raise HTTPException(status_code=400, detail="Service title is required.")

    data["title"] = data["title"].strip()
    data.setdefault("sort_order", 99)
    obj = Service(**data)
    await db.services.insert_one(obj.to_mongo())
    return obj


@admin_content_router.put("/services/{service_id}", response_model=Service)
async def admin_update_service(
    service_id: str,
    input: ServiceIn,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    updates = {k: v for k, v in input.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    if "title" in updates:
        title = (updates["title"] or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Service title cannot be empty.")
        updates["title"] = title

    doc = await db.services.find_one_and_update(
        {"id": service_id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Service not found")
    return Service.from_mongo(doc)


@admin_content_router.delete("/services/{service_id}")
async def admin_delete_service(
    service_id: str,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    result = await db.services.delete_one({"id": service_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"ok": True}


# --- Design Ideas CRUD ---
@admin_content_router.get("/ideas")
async def admin_ideas(_: dict = Depends(require_admin), db=Depends(db_dependency)):
    docs = await db.ideas.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return [DesignIdea.from_mongo(d).model_dump() for d in docs]


@admin_content_router.post("/ideas", response_model=DesignIdea)
async def admin_create_idea(
    input: IdeaIn,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    data = input.model_dump(exclude_unset=True)
    if not (data.get("title") or "").strip():
        raise HTTPException(status_code=400, detail="Idea title is required.")

    data["title"] = data["title"].strip()
    if data.get("category") not in ("homes", "shops", "furniture"):
        data["category"] = "homes"

    obj = DesignIdea(**data)
    await db.ideas.insert_one(obj.to_mongo())
    return obj


@admin_content_router.put("/ideas/{idea_id}", response_model=DesignIdea)
async def admin_update_idea(
    idea_id: str,
    input: IdeaIn,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    updates = {k: v for k, v in input.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")

    if "title" in updates:
        title = (updates["title"] or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Idea title cannot be empty.")
        updates["title"] = title

    if "category" in updates and updates["category"] not in ("homes", "shops", "furniture"):
        updates["category"] = "homes"

    # Check for image replacement to clean up orphan
    old_doc = await db.ideas.find_one({"id": idea_id})
    if not old_doc:
        raise HTTPException(status_code=404, detail="Idea not found")

    new_image = updates.get("image")
    old_image = old_doc.get("image")
    if new_image and old_image and new_image != old_image:
        storage = get_storage(settings)
        await _cleanup_uploaded_image(old_image, db, storage)

    doc = await db.ideas.find_one_and_update(
        {"id": idea_id},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    return DesignIdea.from_mongo(doc)


@admin_content_router.delete("/ideas/{idea_id}")
async def admin_delete_idea(
    idea_id: str,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    doc = await db.ideas.find_one({"id": idea_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Idea not found")

    image_path = doc.get("image")
    if image_path:
        storage = get_storage(settings)
        await _cleanup_uploaded_image(image_path, db, storage)

    await db.ideas.delete_one({"id": idea_id})
    return {"ok": True}


# --- Enquiries CRUD ---
@admin_content_router.get("/enquiries")
async def admin_enquiries(_: dict = Depends(require_admin), db=Depends(db_dependency)):
    docs = await db.enquiries.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return [Enquiry.from_mongo(d).model_dump() for d in docs]


@admin_content_router.put("/admin/enquiries/{enquiry_id}/read")
@admin_content_router.put("/enquiries/{enquiry_id}/read")
async def admin_enquiry_read(
    enquiry_id: str,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    result = await db.enquiries.update_one({"id": enquiry_id}, {"$set": {"read": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return {"ok": True}


@admin_content_router.delete("/admin/enquiries/{enquiry_id}")
@admin_content_router.delete("/enquiries/{enquiry_id}")
async def admin_enquiry_delete(
    enquiry_id: str,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    result = await db.enquiries.delete_one({"id": enquiry_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return {"ok": True}


# --- Settings CRUD ---
@admin_content_router.put("/settings")
async def admin_settings(
    input: SettingsIn,
    request: Request,
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)
    updates = {k: v for k, v in input.model_dump(exclude_unset=True).items() if v is not None}
    updates["updated_at"] = datetime.now(UTC).isoformat()
    await db.settings.update_one({"id": "site"}, {"$set": updates}, upsert=True)
    doc = await db.settings.find_one({"id": "site"})
    return SiteSettings.from_mongo(doc).model_dump()


# --- Photo Upload ---
@admin_content_router.post("/upload")
async def admin_upload(
    request: Request,
    file: UploadFile = File(...),
    _: dict = Depends(require_admin),
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    verify_csrf(request, settings)

    # 1. Read in chunks, enforce max size of 8 MB
    buffer = io.BytesIO()
    total_size = 0
    chunk_size = 64 * 1024  # 64 KB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="Image must be smaller than 8 MB.")
        buffer.write(chunk)

    raw_data = buffer.getvalue()
    if not raw_data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 2. Pillow verification & format check
    try:
        img = Image.open(io.BytesIO(raw_data))
        img_format = (img.format or "").upper()
    except Exception:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or WEBP images are allowed.")

    format_mapping = {
        "JPEG": ("jpg", "image/jpeg"),
        "PNG": ("png", "image/png"),
        "WEBP": ("webp", "image/webp"),
    }
    if img_format not in format_mapping:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or WEBP images are allowed.")

    file_ext, target_content_type = format_mapping[img_format]

    # 3. Auto-orient by EXIF orientation
    with contextlib.suppress(Exception):
        img = ImageOps.exif_transpose(img)

    # 4. Resize if longest side > 2000px
    max_dimension = 2000
    w, h = img.size
    if max(w, h) > max_dimension:
        if w > h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 5. Re-encode cleanly (stripping EXIF / GPS metadata)
    output_io = io.BytesIO()
    if img_format == "JPEG":
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output_io, format="JPEG", quality=85, optimize=True)
    elif img_format == "PNG":
        img.save(output_io, format="PNG", optimize=True)
    elif img_format == "WEBP":
        img.save(output_io, format="WEBP", quality=85)

    processed_bytes = output_io.getvalue()

    # 6. Save to storage
    file_id = str(uuid.uuid4())
    storage_path = f"uploads/{file_id}.{file_ext}"
    storage = get_storage(settings)

    try:
        await storage.save(storage_path, processed_bytes, target_content_type)
    except Exception as exc:
        logger.error("Storage save failed for %s: %s", storage_path, exc)
        raise HTTPException(status_code=500, detail="Failed to store uploaded file.")

    # 7. Record in files collection
    await db.files.insert_one({
        "id": file_id,
        "storage_path": storage_path,
        "original_filename": file.filename or "",
        "content_type": target_content_type,
        "size": len(processed_bytes),
        "is_deleted": False,
        "created_at": datetime.now(UTC).isoformat(),
    })

    return {"path": storage_path, "url": f"/api/files/{storage_path}"}
