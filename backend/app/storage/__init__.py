import logging

from app.config import Settings, get_settings
from app.storage.base import Storage
from app.storage.local import LocalStorage
from app.storage.r2 import R2Storage

logger = logging.getLogger("anweshan.storage")

_storage: Storage | None = None


def get_storage(settings: Settings | None = None) -> Storage:
    global _storage
    if _storage is not None:
        return _storage

    s = settings or get_settings()
    if s.STORAGE_BACKEND == "r2":
        if not (s.R2_ACCOUNT_ID and s.R2_ACCESS_KEY_ID and s.R2_SECRET_ACCESS_KEY and s.R2_BUCKET):
            logger.warning("R2 credentials incomplete. Falling back to local storage.")
            _storage = LocalStorage(s.resolved_upload_dir)
        else:
            logger.info("Initializing Cloudflare R2 storage on bucket %s", s.R2_BUCKET)
            _storage = R2Storage(
                account_id=s.R2_ACCOUNT_ID,
                access_key_id=s.R2_ACCESS_KEY_ID,
                secret_access_key=s.R2_SECRET_ACCESS_KEY,
                bucket=s.R2_BUCKET,
            )
    else:
        logger.info("Initializing local storage at %s", s.resolved_upload_dir)
        _storage = LocalStorage(s.resolved_upload_dir)

    return _storage


def reset_storage() -> None:
    global _storage
    _storage = None
