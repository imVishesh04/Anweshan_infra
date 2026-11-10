import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field


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

        if len(name) < 2 or len(name) > 80:
            raise HTTPException(status_code=400, detail="Please enter your name.")

        # Phone digits count must be between 10 and 13 digits, allowing +, spaces, -
        digits_only = re.sub(r"\D", "", phone)
        if len(digits_only) < 10 or len(digits_only) > 13 or not re.fullmatch(r"[0-9+\-\s]{10,20}", phone):
            raise HTTPException(status_code=400, detail="Please enter a valid phone number.")

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
