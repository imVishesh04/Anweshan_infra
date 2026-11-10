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
    return SiteSettings.from_mongo(doc).model_dump() if doc else SiteSettings().model_dump()


@public_router.get("/services")
async def get_services(db=Depends(db_dependency)):
    docs = await db.services.find({}, {"_id": 0}).sort([("sort_order", ASCENDING)]).to_list(100)
    return [Service.from_mongo(d).model_dump() for d in docs if d.get("active", True)]


@public_router.get("/ideas")
async def get_ideas(category: str | None = None, db=Depends(db_dependency)):
    query = {"category": category} if category in ("homes", "shops", "furniture") else {}
    docs = await db.ideas.find(query, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return [DesignIdea.from_mongo(d).model_dump() for d in docs]


@public_router.post("/enquiries", response_model=Enquiry)
async def create_enquiry(
    input: EnquiryIn,
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    ip = request.client.host if request.client else "unknown"
    await check_and_increment_enquiry_limit(db, ip)

    validated = EnquiryIn.validated(input.model_dump())
    enquiry = Enquiry(**validated.model_dump())
    await db.enquiries.insert_one(enquiry.to_mongo())

    background_tasks.add_task(send_lead_notifications, enquiry.model_dump(), settings)
    return enquiry


@public_router.get("/files/{path:path}")
async def serve_file(
    path: str,
    db=Depends(db_dependency),
    settings: Settings = Depends(get_settings),
):
    storage = get_storage(settings)
    try:
        data, content_type = await storage.open(path)
    except (FileNotFoundError, PermissionError):
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as exc:
        logger.error("Error opening file %s: %s", path, exc)
        raise HTTPException(status_code=404, detail="File not found")

    record = await db.files.find_one({"storage_path": path, "is_deleted": False})
    media_type = record.get("content_type") if record else content_type

    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )
