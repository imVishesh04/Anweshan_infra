import logging
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.phone import normalize_phone

logger = logging.getLogger("anweshan.models")


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
        d.pop("_id", None)  # Never expose MongoDB internal _id
        # Imported or hand-edited records may hold real datetimes; the API uses ISO strings.
        for key, value in d.items():
            if isinstance(value, datetime):
                d[key] = (value if value.tzinfo else value.replace(tzinfo=UTC)).isoformat()
        return cls(**d)

    @classmethod
    def list_from_mongo(cls, docs) -> list[dict]:
        """Convert a list of documents, skipping (and logging) any broken record
        instead of failing the whole page with a 500."""
        out = []
        for doc in docs:
            try:
                out.append(cls.from_mongo(doc).model_dump())
            except (ValidationError, TypeError, ValueError) as exc:
                logger.error("Skipping invalid %s record %s: %s", cls.__name__, doc.get("id"), exc)
        return out


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
    title: str | None = None
    description: str | None = None
    price: str | None = None
    timeline: str | None = None
    icon: str | None = None
    image: str | None = None
    active: bool | None = None
    sort_order: int | None = None


class DesignIdea(BaseDocument):
    title: str
    category: str = "homes"
    description: str = ""
    image: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class IdeaIn(BaseModel):
    title: str | None = None
    category: str | None = None
    description: str | None = None
    image: str | None = None


class Enquiry(BaseDocument):
    name: str
    phone: str
    service: str = ""
    message: str = ""
    source: str = "website"  # "website" or "whatsapp"
    read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class EnquiryIn(BaseModel):
    name: str
    phone: str
    service: str = ""
    message: str = ""

    @classmethod
    def validated(cls, data: dict) -> "EnquiryIn":
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()
        service = (data.get("service") or "").strip()[:100]
        message = (data.get("message") or "").strip()[:1000]

        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Please enter your name.")
        if len(name) > 80:
            raise HTTPException(status_code=400, detail="Name is too long (max 80 letters).")

        # Accept common shapes ("98765 43210", "098765-43210", "(+91) 98765 43210")
        # and store one standard form so call / WhatsApp links always work.
        normalized = normalize_phone(phone) if len(phone) <= 24 else None
        if normalized is None:
            raise HTTPException(status_code=400, detail="Please enter a valid 10-digit phone number.")
        phone = normalized

        return cls(name=name, phone=phone, service=service, message=message)


class SiteSettings(BaseDocument):
    id: str = "site"
    phone: str = ""
    whatsapp: str = ""
    instagram: str = ""
    address: str = ""
    hours: str = ""
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SettingsIn(BaseModel):
    phone: str | None = None
    whatsapp: str | None = None
    instagram: str | None = None
    address: str | None = None
    hours: str | None = None


class LoginIn(BaseModel):
    password: str


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str


class User(BaseDocument):
    email: str
    password_hash: str
    role: str = "admin"
    token_version: int = 1
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class FileRecord(BaseDocument):
    storage_path: str
    original_filename: str = ""
    content_type: str = "application/octet-stream"
    size: int = 0
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
