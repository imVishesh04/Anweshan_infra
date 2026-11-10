import contextlib
import io
import logging
import uuid
import warnings
from datetime import UTC, datetime

import anyio
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
from app.phone import normalize_instagram, require_phone
from app.security import require_admin, verify_csrf
from app.storage import get_storage

logger = logging.getLogger("anweshan.admin_content")

admin_content_router = APIRouter(prefix="/api/admin", tags=["admin-content"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB
Image.MAX_IMAGE_PIXELS = 25_000_000  # Sane decompression bomb limit


class ImageRejected(ValueError):
    """Raised with a message the admin user can understand."""


_FORMATS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}
MAX_DIMENSION = 2000


def _process_image(raw_data: bytes) -> tuple[bytes, str, str]:
    with warnings.catch_warnings():
        # Treat "very large image" warnings as errors instead of silently accepting them.
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            img = Image.open(io.BytesIO(raw_data))
            img_format = (img.format or "").upper()
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ImageRejected("This photo's resolution is too high. Please use a smaller photo.")
        except Exception:
            raise ImageRejected(
                "Only JPG, PNG or WEBP photos are allowed. On iPhone, set Camera > Formats to 'Most Compatible'."
            )

        if img_format not in _FORMATS:
            raise ImageRejected(
                "Only JPG, PNG or WEBP photos are allowed. On iPhone, set Camera > Formats to 'Most Compatible'."
            )
        file_ext, content_type = _FORMATS[img_format]

        try:
            if img_format == "JPEG":
                # Let the JPEG decoder skip detail we would throw away anyway.
                img.draft("RGB", (MAX_DIMENSION, MAX_DIMENSION))
            img.load()
            with contextlib.suppress(Exception):
                img = ImageOps.exif_transpose(img)
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

            # Re-encode cleanly (this also strips EXIF / GPS location data)
            out = io.BytesIO()
            if img_format == "JPEG":
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(out, format="JPEG", quality=85, optimize=True)
            elif img_format == "PNG":
                img.save(out, format="PNG", optimize=True)
            else:
                img.save(out, format="WEBP", quality=85)
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ImageRejected("This photo's resolution is too high. Please use a smaller photo.")
        except (OSError, ValueError, SyntaxError):
            raise ImageRejected("This photo file seems damaged. Please try another photo.")

    return out.getvalue(), file_ext, content_type


async def _cleanup_uploaded_image(image_path: str | None, db, storage) -> None:
    """Delete an uploaded photo once nothing (idea or service) uses it any more."""
    if not image_path or image_path.startswith("http"):
        return
    still_used = await db.ideas.count_documents({"image": image_path}) + await db.services.count_documents(
        {"image": image_path}
    )
    if still_used:
        return
    file_doc = await db.files.find_one({"storage_path": image_path, "is_deleted": False})
    if file_doc:
        await db.files.update_one({"storage_path": image_path}, {"$set": {"is_deleted": True}})
        try:
            await storage.delete(image_path)
        except Exception as exc:
            logger.error("Could not delete stored file %s: %s", image_path, type(exc).__name__)
        logger.info("Cleaned up unused uploaded file: %s", image_path)


# --- Services CRUD ---
@admin_content_router.get("/services")
async def admin_services(_: dict = Depends(require_admin), db=Depends(db_dependency)):
    docs = await db.services.find({}, {"_id": 0}).sort([("sort_order", ASCENDING)]).to_list(100)
    return Service.list_from_mongo(docs)


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
    doc = await db.services.find_one_and_delete({"id": service_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Service not found")
    await _cleanup_uploaded_image(doc.get("image"), db, get_storage(settings))
    return {"ok": True}


# --- Design Ideas CRUD ---
@admin_content_router.get("/ideas")
async def admin_ideas(_: dict = Depends(require_admin), db=Depends(db_dependency)):
    docs = await db.ideas.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(500)
    return DesignIdea.list_from_mongo(docs)


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

    # An empty photo field means "keep the current photo", never "remove it".
    if "image" in updates and not str(updates["image"]).strip():
        updates.pop("image")
        if not updates:
            raise HTTPException(status_code=400, detail="Nothing to update.")

    old_doc = await db.ideas.find_one_and_update(
        {"id": idea_id},
        {"$set": updates},
        return_document=ReturnDocument.BEFORE,
    )
    if not old_doc:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Remove the replaced photo only after the idea points at the new one.
    old_image = old_doc.get("image")
    if "image" in updates and old_image and updates["image"] != old_image:
        await _cleanup_uploaded_image(old_image, db, get_storage(settings))

    doc = await db.ideas.find_one({"id": idea_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Idea not found")
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

    await db.ideas.delete_one({"id": idea_id})
    await _cleanup_uploaded_image(doc.get("image"), db, get_storage(settings))
    return {"ok": True}


# --- Enquiries CRUD ---
@admin_content_router.get("/enquiries")
async def admin_enquiries(_: dict = Depends(require_admin), db=Depends(db_dependency)):
    docs = await db.enquiries.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(1000)
    return Enquiry.list_from_mongo(docs)


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
    # Phone / WhatsApp are used to build every call and WhatsApp button on the site,
    # so they must never be saved empty or in a shape the links cannot use.
    if "phone" in updates:
        updates["phone"] = require_phone(updates["phone"], "phone number")
    if "whatsapp" in updates:
        updates["whatsapp"] = require_phone(updates["whatsapp"], "WhatsApp number")
    if "instagram" in updates:
        updates["instagram"] = normalize_instagram(updates["instagram"])
    for key in ("address", "hours"):
        if key in updates:
            updates[key] = updates[key].strip()[:300]
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

    # 2-5. Decode, rotate, resize and re-encode in a worker thread: this takes
    # 0.3+ s for a phone photo and would otherwise freeze the site for everyone.
    try:
        processed_bytes, file_ext, target_content_type = await anyio.to_thread.run_sync(
            _process_image, raw_data
        )
    except ImageRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc))

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
