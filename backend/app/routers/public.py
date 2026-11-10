import hashlib
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)
from pymongo import ASCENDING, DESCENDING

from app.config import Settings, get_settings
from app.db import db_dependency
from app.models import DesignIdea, Enquiry, EnquiryIn, Service, SiteSettings
from app.notify import send_lead_notifications
from app.ratelimit import check_and_increment_enquiry_limit
from app.security import get_client_ip
from app.storage import get_storage

logger = logging.getLogger("anweshan.public")

public_router = APIRouter(prefix="/api", tags=["public"])


@public_router.get("/")
async def root():
    return {"message": "ANWESHAN Infra API"}


@public_router.get("/health")
async def health_check():
    return {"status": "ok"}


@public_router.get("/ready")
async def readiness_check(db=Depends(db_dependency)):
    try:
        await db.command("ping")
        return {"status": "ready"}
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable")


@public_router.get("/site")
async def get_site(db=Depends(db_dependency)):
    doc = await db.settings.find_one({"id": "site"})
    try:
        return SiteSettings.from_mongo(doc).model_dump() if doc else SiteSettings().model_dump()
    except Exception as exc:
        logger.error("Invalid site settings record: %s", exc)
        return SiteSettings().model_dump()


@public_router.get("/services")
async def get_services(db=Depends(db_dependency)):
    docs = await db.services.find({}, {"_id": 0}).sort([("sort_order", ASCENDING)]).to_list(100)
    return Service.list_from_mongo([d for d in docs if d.get("active", True)])


@public_router.get("/ideas")
async def get_ideas(category: str | None = None, db=Depends(db_dependency)):
    query = {"category": category} if category in ("homes", "shops", "furniture") else {}
    docs = await db.ideas.find(query, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return DesignIdea.list_from_mongo(docs)


@public_router.post("/enquiries", response_model=Enquiry)
async def create_enquiry(
    input: EnquiryIn,
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    # Validate first: a customer who mistypes their number should not use up
    # their enquiry limit.
    validated = EnquiryIn.validated(input.model_dump())
    await check_and_increment_enquiry_limit(db, get_client_ip(request, settings))

    enquiry = Enquiry(**validated.model_dump())
    await db.enquiries.insert_one(enquiry.to_mongo())

    background_tasks.add_task(send_lead_notifications, enquiry.model_dump(), settings)
    return enquiry


# Only these folders hold website photos; anything else in the bucket is never served.
SERVABLE_PREFIXES = ("uploads/", "aurelia-interiors/")
SERVABLE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@public_router.get("/files/{path:path}")
async def serve_file(
    path: str,
    request: Request,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    if not path.startswith(SERVABLE_PREFIXES) or ".." in path:
        raise HTTPException(status_code=404, detail="File not found")

    storage = get_storage(settings)
    try:
        data, content_type = await storage.open(path)
    except (FileNotFoundError, PermissionError):
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as exc:
        logger.error("Storage error opening %s: %s", path, type(exc).__name__)
        raise HTTPException(status_code=503, detail="Photo temporarily unavailable")

    record = await db.files.find_one({"storage_path": path, "is_deleted": False})
    media_type = (record.get("content_type") if record else None) or content_type
    if media_type not in SERVABLE_TYPES:
        raise HTTPException(status_code=404, detail="File not found")

    # An ETag lets browsers and Netlify's CDN reuse the photo instead of
    # fetching it from Railway and R2 on every page view.
    etag = '"' + hashlib.md5(data, usedforsecurity=False).hexdigest() + '"'
    headers = {
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
        "ETag": etag,
    }
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content=data, media_type=media_type, headers=headers)
