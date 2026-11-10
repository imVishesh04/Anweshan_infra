import os
import re
import uuid
import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List

import bcrypt
import jwt
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
JWT_SECRET = os.environ['JWT_SECRET']
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@aurelia.design')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'aurelia2026')

STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "aurelia-interiors"

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

INDEXES: dict[str, list[IndexModel]] = {
    "services": [IndexModel([("sort_order", ASCENDING)], name="sort_order_asc")],
    "ideas": [IndexModel([("created_at", DESCENDING)], name="created_at_desc"), IndexModel([("category", ASCENDING)], name="category_asc")],
    "enquiries": [IndexModel([("created_at", DESCENDING)], name="created_at_desc"), IndexModel([("read", ASCENDING)], name="read_asc")],
    "files": [IndexModel([("storage_path", ASCENDING)], name="storage_path", unique=True)],
    "users": [IndexModel([("email", ASCENDING)], name="email", unique=True)],
    "login_attempts": [IndexModel([("identifier", ASCENDING)], name="identifier")],
}

async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)

# ---------------- Object storage (Emergent) ----------------
storage_key = None

def init_storage(force: bool = False):
    global storage_key
    if storage_key and not force:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120,
    )
    if resp.status_code in (400, 404):
        init_storage(force=True)
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": storage_key, "Content-Type": content_type},
            data=data, timeout=120,
        )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple[bytes, str]:
    key = init_storage()
    resp = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# ---------------- Models ----------------
class BaseDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def to_mongo(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_mongo(cls, doc):
        if not doc:
            return None
        d = dict(doc)
        d.pop("_id", None)  # never serialize raw ObjectId
        return cls(**d)

class Service(BaseDocument):
    title: str
    description: str = ""
    price: str = ""
    timeline: str = ""
    icon: str = "home"
    image: str = ""
    active: bool = True
    sort_order: int = 0

class ServiceIn(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    timeline: Optional[str] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    active: Optional[bool] = None
    sort_order: Optional[int] = None

class DesignIdea(BaseDocument):
    title: str
    category: str = "homes"
    description: str = ""
    image: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class IdeaIn(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

class Enquiry(BaseDocument):
    name: str
    phone: str
    service: str = ""
    message: str = ""
    read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EnquiryIn(BaseModel):
    name: str
    phone: str
    service: str = ""
    message: str = ""

    @classmethod
    def validated(cls, data: dict):
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Please enter your name.")
        if not re.fullmatch(r"[0-9+\-\s]{7,15}", phone):
            raise HTTPException(status_code=400, detail="Please enter a valid phone number.")
        return cls(name=name, phone=phone, service=(data.get("service") or "").strip(), message=(data.get("message") or "").strip()[:1000])

class SiteSettings(BaseDocument):
    id: str = "site"
    phone: str = ""
    whatsapp: str = ""
    instagram: str = ""
    address: str = ""
    hours: str = ""
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SettingsIn(BaseModel):
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    instagram: Optional[str] = None
    address: Optional[str] = None
    hours: Optional[str] = None

class LoginIn(BaseModel):
    password: str

# ---------------- Auth helpers ----------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False

def create_access_token() -> str:
    payload = {"sub": ADMIN_EMAIL, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def create_refresh_token() -> str:
    payload = {"sub": ADMIN_EMAIL, "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie("access_token", access, httponly=True, secure=True, samesite="none", max_age=900, path="/")
    response.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="none", max_age=604800, path="/")

async def require_admin(request: Request) -> None:
    token = request.cookies.get("access_token")
    if not token:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def _as_dt(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None

async def login_locked(ip: str) -> None:
    rec = await db.login_attempts.find_one({"identifier": ip})
    if not rec:
        return
    locked_until = _as_dt(rec.get("locked_until"))
    if locked_until and datetime.now(timezone.utc) < locked_until:
        raise HTTPException(status_code=429, detail="Too many wrong attempts. Please try again in 15 minutes.")

async def register_failed_attempt(ip: str) -> None:
    now = datetime.now(timezone.utc)
    rec = await db.login_attempts.find_one({"identifier": ip})
    count = (rec or {}).get("count", 0) + 1
    update = {"count": count, "updated_at": now.isoformat()}
    if count >= 5:
        update["locked_until"] = (now + timedelta(minutes=15)).isoformat()
        update["count"] = 0
    await db.login_attempts.update_one({"identifier": ip}, {"$set": update, "$setOnInsert": {"created_at": now.isoformat()}}, upsert=True)

# ---------------- App & CORS ----------------
app = FastAPI()
api_router = APIRouter(prefix="/api")

origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip() and o.strip() != '*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:3000"],
    allow_origin_regex=r"https://([a-z0-9-]+\.)?emergentagent\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Public routes ----------------
@api_router.get("/")
async def root():
    return {"message": "AURELIA Interiors API"}

@api_router.get("/site")
async def get_site():
    doc = await db.settings.find_one({"id": "site"})
    return SiteSettings.from_mongo(doc).model_dump() if doc else SiteSettings().model_dump()

@api_router.get("/services")
async def get_services():
    docs = await db.services.find({}, {"_id": 0}).sort([("sort_order", ASCENDING)]).to_list(100)
    return [Service.from_mongo(d).model_dump() for d in docs if d.get("active", True)]

@api_router.get("/ideas")
async def get_ideas(category: Optional[str] = None):
    query = {"category": category} if category in ("homes", "shops", "furniture") else {}
    docs = await db.ideas.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return [DesignIdea.from_mongo(d).model_dump() for d in docs]

@api_router.post("/enquiries", response_model=Enquiry)
async def create_enquiry(input: EnquiryIn):
    obj = EnquiryIn.validated(input.model_dump())
    enquiry = Enquiry(**obj.model_dump())
    await db.enquiries.insert_one(enquiry.to_mongo())
    try:
        notify_owner_whatsapp(enquiry)
    except Exception as exc:
        logger.error("whatsapp notify failed: %s", exc)
    return enquiry

# ---------------- WhatsApp lead alert (Twilio) ----------------
def notify_owner_whatsapp(enquiry: Enquiry) -> None:
    """Fire-and-forget: pings the owner's WhatsApp via Twilio when configured."""
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_num = os.environ.get("TWILIO_WHATSAPP_FROM")
    if not (sid and token and from_num):
        logger.info("twilio not configured - skipping whatsapp alert")
        return
    from twilio.rest import Client

    body = (
        "New Enquiry — ANWESHAN Infra\n"
        f"Name: {enquiry.name}\n"
        f"Phone: {enquiry.phone}\n"
        f"Service: {enquiry.service or 'Not chosen'}\n"
        f"Message: {enquiry.message or '-'}\n"
        "Open your website admin to reply."
    )
    try:
        client = Client(sid, token)
        msg = client.messages.create(
            from_=f"whatsapp:{from_num}",
            to="whatsapp:+918658429239",
            body=body,
        )
        logger.info("whatsapp alert sent: %s", msg.sid)
    except Exception as exc:
        logger.error("twilio whatsapp error: %s", exc)

@api_router.get("/files/{path:path}")
async def serve_file(path: str):
    record = await db.files.find_one({"storage_path": path, "is_deleted": False})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        data, content_type = get_object(path)
    except Exception:
        raise HTTPException(status_code=502, detail="Storage unavailable")
    return Response(content=data, media_type=record.get("content_type") or content_type,
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})

# ---------------- Admin auth ----------------
@api_router.post("/admin/login")
async def admin_login(body: LoginIn, request: Request, response: Response):
    ip = request.client.host if request.client else "unknown"
    await login_locked(ip)
    admin = await db.users.find_one({"role": "admin"})
    if not admin or not verify_password(body.password, admin.get("password_hash", "")):
        await register_failed_attempt(ip)
        raise HTTPException(status_code=401, detail="Wrong password. Please try again.")
    await db.login_attempts.delete_one({"identifier": ip})
    set_auth_cookies(response, create_access_token(), create_refresh_token())
    return {"ok": True, "email": admin.get("email")}

@api_router.post("/admin/refresh")
async def admin_refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    set_auth_cookies(response, create_access_token(), create_refresh_token())
    return {"ok": True}

@api_router.post("/admin/logout")
async def admin_logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}

@api_router.get("/admin/me")
async def admin_me(_: None = Depends(require_admin)):
    return {"ok": True, "email": ADMIN_EMAIL}

# ---------------- Admin CRUD ----------------
@api_router.get("/admin/services")
async def admin_services(_: None = Depends(require_admin)):
    docs = await db.services.find({}, {"_id": 0}).sort([("sort_order", ASCENDING)]).to_list(100)
    return [Service.from_mongo(d).model_dump() for d in docs]

@api_router.post("/admin/services", response_model=Service)
async def admin_create_service(input: ServiceIn, _: None = Depends(require_admin)):
    data = input.model_dump(exclude_unset=True)
    if not (data.get("title") or "").strip():
        raise HTTPException(status_code=400, detail="Service title is required.")
    data["title"] = data["title"].strip()
    data.setdefault("sort_order", 99)
    obj = Service(**data)
    await db.services.insert_one(obj.to_mongo())
    return obj

@api_router.put("/admin/services/{service_id}", response_model=Service)
async def admin_update_service(service_id: str, input: ServiceIn, _: None = Depends(require_admin)):
    updates = {k: v for k, v in input.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    doc = await db.services.find_one_and_update({"id": service_id}, {"$set": updates}, return_document=True)
    if not doc:
        raise HTTPException(status_code=404, detail="Service not found")
    return Service.from_mongo(doc)

@api_router.delete("/admin/services/{service_id}")
async def admin_delete_service(service_id: str, _: None = Depends(require_admin)):
    result = await db.services.delete_one({"id": service_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"ok": True}

@api_router.get("/admin/ideas")
async def admin_ideas(_: None = Depends(require_admin)):
    docs = await db.ideas.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return [DesignIdea.from_mongo(d).model_dump() for d in docs]

@api_router.post("/admin/ideas", response_model=DesignIdea)
async def admin_create_idea(input: IdeaIn, _: None = Depends(require_admin)):
    data = input.model_dump(exclude_unset=True)
    if not (data.get("title") or "").strip():
        raise HTTPException(status_code=400, detail="Idea title is required.")
    data["title"] = data["title"].strip()
    if data.get("category") not in ("homes", "shops", "furniture"):
        data["category"] = "homes"
    obj = DesignIdea(**data)
    await db.ideas.insert_one(obj.to_mongo())
    return obj

@api_router.put("/admin/ideas/{idea_id}", response_model=DesignIdea)
async def admin_update_idea(idea_id: str, input: IdeaIn, _: None = Depends(require_admin)):
    updates = {k: v for k, v in input.model_dump(exclude_unset=True).items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update.")
    doc = await db.ideas.find_one_and_update({"id": idea_id}, {"$set": updates}, return_document=True)
    if not doc:
        raise HTTPException(status_code=404, detail="Idea not found")
    return DesignIdea.from_mongo(doc)

@api_router.delete("/admin/ideas/{idea_id}")
async def admin_delete_idea(idea_id: str, _: None = Depends(require_admin)):
    result = await db.ideas.delete_one({"id": idea_id})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {"ok": True}

@api_router.get("/admin/enquiries")
async def admin_enquiries(_: None = Depends(require_admin)):
    docs = await db.enquiries.find({}, {"_id": 0}).sort([("created_at", DESCENDING)]).to_list(200)
    return [Enquiry.from_mongo(d).model_dump() for d in docs]

@api_router.put("/admin/enquiries/{enquiry_id}/read")
async def admin_enquiry_read(enquiry_id: str, _: None = Depends(require_admin)):
    await db.enquiries.update_one({"id": enquiry_id}, {"$set": {"read": True}})
    return {"ok": True}

@api_router.delete("/admin/enquiries/{enquiry_id}")
async def admin_enquiry_delete(enquiry_id: str, _: None = Depends(require_admin)):
    await db.enquiries.delete_one({"id": enquiry_id})
    return {"ok": True}

@api_router.put("/admin/settings")
async def admin_settings(input: SettingsIn, _: None = Depends(require_admin)):
    updates = {k: v for k, v in input.model_dump(exclude_unset=True).items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.settings.update_one({"id": "site"}, {"$set": updates}, upsert=True)
    doc = await db.settings.find_one({"id": "site"})
    return SiteSettings.from_mongo(doc).model_dump()

ALLOWED_UPLOAD_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

@api_router.post("/admin/upload")
async def admin_upload(file: UploadFile = File(...), _: None = Depends(require_admin)):
    ext = ALLOWED_UPLOAD_TYPES.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or WEBP images are allowed.")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be smaller than 8 MB.")
    path = f"{APP_NAME}/uploads/{uuid.uuid4()}.{ext}"
    try:
        result = put_object(path, data, file.content_type)
    except Exception as exc:
        logger.error("upload failed: %s", exc)
        raise HTTPException(status_code=502, detail="Upload failed. Please try again.")
    await db.files.insert_one({
        "id": str(uuid.uuid4()),
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": result.get("size", len(data)),
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"path": result["path"], "url": f"/api/files/{result['path']}"}

app.include_router(api_router)

# ---------------- Seeds ----------------
SEED_SERVICES = [
    {"title": "Full Home Interiors", "description": "Every room designed and built for you — living room, kitchen, bedrooms and bathrooms. You approve the 3D design first, we handle the rest.", "price": "\u20b91,80,000 onwards", "timeline": "45\u201390 days", "icon": "home", "image": "https://images.unsplash.com/photo-1632120377007-c2adc3017b1e?crop=entropy&cs=srgb&fm=jpg&q=85", "sort_order": 1},
    {"title": "Shop & Retail Interiors", "description": "Boutique stores, caf\u00e9s, salons and offices that pull customers in and make them stay longer.", "price": "\u20b92,50,000 onwards", "timeline": "30\u201360 days", "icon": "shop", "image": "https://images.unsplash.com/photo-1551887196-72e32bfc7bf3?crop=entropy&cs=srgb&fm=jpg&q=85", "sort_order": 2},
    {"title": "Furniture Assessment", "description": "We visit your home, check your furniture and woodwork, and tell you honestly what to repair, polish or remake.", "price": "Free first visit", "timeline": "1 day", "icon": "armchair", "image": "https://images.unsplash.com/photo-1768144092684-c1a5dd6c7aad?crop=entropy&cs=srgb&fm=jpg&q=85", "sort_order": 3},
]

SEED_IDEAS = [
    {"title": "Warm Cream Living Room", "category": "homes", "description": "Soft creams, brass lamps and a statement arch \u2014 a living room that feels calm and expensive.", "image": "https://images.unsplash.com/photo-1632120377007-c2adc3017b1e?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"title": "Classic Arch Nook", "category": "homes", "description": "Dark wood panelling, warm lighting and a cosy reading corner.", "image": "https://images.unsplash.com/photo-1700226034367-2fb120f48dfa?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"title": "Modern Minimal Lounge", "category": "homes", "description": "Clean lines, muted tones and layered textures for a restful space.", "image": "https://images.unsplash.com/photo-1758915753451-b478b4e6f920?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"title": "Boutique Caf\u00e9 with Plants", "category": "shops", "description": "Hanging greens, warm bulbs and a counter built to be photographed.", "image": "https://images.unsplash.com/photo-1551887196-72e32bfc7bf3?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"title": "Bakery & Caf\u00e9 Counter", "category": "shops", "description": "Fresh green tiles, open display and a flow that keeps queues moving.", "image": "https://images.unsplash.com/photo-1601205741712-b261aff33a7d?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"title": "Handcrafted Wood Chair", "category": "furniture", "description": "Solid wood, hand-finished \u2014 assess, polish or remake, we tell you honestly.", "image": "https://images.unsplash.com/photo-1768144092684-c1a5dd6c7aad?crop=entropy&cs=srgb&fm=jpg&q=85"},
    {"title": "Sculpted Comfort Seat", "category": "furniture", "description": "Comfort-first curves in warm upholstery.", "image": "https://images.unsplash.com/photo-1762545078318-8443881c2d83?crop=entropy&cs=srgb&fm=jpg&q=85"},
]

async def seed_data() -> None:
    if await db.users.find_one({"role": "admin"}) is None:
        await db.users.insert_one({
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD),
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Seeded admin user")
    if await db.settings.find_one({"id": "site"}) is None:
        await db.settings.insert_one(SiteSettings(
            phone="+91 86584 29239",
            whatsapp="+91 86584 29239",
            instagram="https://www.instagram.com/anweshaninfra",
        ).to_mongo())
        logger.info("Seeded site settings")
    if await db.services.count_documents({}) == 0:
        for s in SEED_SERVICES:
            await db.services.insert_one(Service(**s).to_mongo())
        logger.info("Seeded services")
    if await db.ideas.count_documents({}) == 0:
        for i in SEED_IDEAS:
            await db.ideas.insert_one(DesignIdea(**i).to_mongo())
        logger.info("Seeded design ideas")

@app.on_event("startup")
async def startup():
    app.state.index_task = asyncio.create_task(ensure_indexes())
    await seed_data()
    if EMERGENT_KEY:
        try:
            init_storage()
            logger.info("Storage initialized")
        except Exception as e:
            logger.error("Storage init failed: %s", e)
    else:
        logger.warning("EMERGENT_LLM_KEY not set - image upload disabled")

@app.on_event("shutdown")
async def shutdown_db_client():
    app.state.index_task.cancel()
    with suppress(asyncio.CancelledError):
        await app.state.index_task
    client.close()
