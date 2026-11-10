"""Phone number and Instagram link helpers.

Customers and the owner type numbers in many shapes ("98765 43210",
"098765-43210", "+91 98765 43210"). WhatsApp (wa.me) and tel: links need the
full international number, so numbers are normalised once, when saved.
"""

import re

from fastapi import HTTPException

_ALLOWED_PHONE_CHARS = re.compile(r"[0-9+\-(). ]+")


def normalize_phone(raw: str | None) -> str | None:
    """Return "+91 98765 43210" for Indian numbers, "+<digits>" for others.

    Returns None when the value does not look like a phone number.
    """
    s = (raw or "").strip()
    if not s or not _ALLOWED_PHONE_CHARS.fullmatch(s):
        return None

    digits = re.sub(r"\D", "", s)
    has_plus = s.startswith("+")
    if not has_plus and digits.startswith("00"):
        digits, has_plus = digits[2:], True
    if not has_plus and len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if not has_plus and len(digits) == 10:
        digits = "91" + digits

    if len(digits) < 11 or len(digits) > 15:
        return None
    if digits.startswith("91") and len(digits) == 12:
        return f"+91 {digits[2:7]} {digits[7:]}"
    return f"+{digits}"


def require_phone(raw: str | None, field_label: str) -> str:
    value = normalize_phone(raw)
    if value is None:
        raise HTTPException(status_code=400, detail=f"Please enter a valid {field_label}.")
    return value


def normalize_instagram(raw: str | None) -> str:
    """Turn "@handle", "handle" or "instagram.com/handle" into a full https link."""
    s = (raw or "").strip()
    if not s:
        return ""
    if s.lower().startswith(("http://", "https://")):
        if "instagram.com/" not in s.lower():
            raise HTTPException(status_code=400, detail="Please enter an Instagram link or @username.")
        return "https://" + s.split("://", 1)[1]
    if "instagram.com/" in s.lower():
        return "https://" + s.lstrip("/")
    handle = s.lstrip("@").strip("/")
    if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", handle):
        raise HTTPException(status_code=400, detail="Please enter an Instagram link or @username.")
    return f"https://www.instagram.com/{handle}"
