import logging

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, IndexModel

logger = logging.getLogger("anweshan.db")

_client: AsyncMongoClient | None = None
_db = None

INDEXES: dict[str, list[IndexModel]] = {
    "services": [
        IndexModel([("sort_order", ASCENDING)], name="sort_order_asc"),
    ],
    "ideas": [
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
        IndexModel([("category", ASCENDING)], name="category_asc"),
    ],
    "enquiries": [
        IndexModel([("created_at", DESCENDING)], name="created_at_desc"),
        IndexModel([("read", ASCENDING)], name="read_asc"),
    ],
    "files": [
        IndexModel([("storage_path", ASCENDING)], name="storage_path_uniq", unique=True),
    ],
    "users": [
        IndexModel([("email", ASCENDING)], name="email_uniq", unique=True),
    ],
    "login_attempts": [
        IndexModel([("identifier", ASCENDING)], name="identifier_asc"),
        IndexModel([("expires_at", ASCENDING)], name="login_attempts_ttl", expireAfterSeconds=0),
    ],
    "enquiry_rate_limits": [
        IndexModel([("ip", ASCENDING)], name="ip_asc"),
        IndexModel([("expires_at", ASCENDING)], name="enquiry_limits_ttl", expireAfterSeconds=0),
    ],
}


async def ensure_indexes(db) -> None:
    for collection_name, models in INDEXES.items():
        for model in models:
            try:
                await db[collection_name].create_indexes([model])
            except Exception as exc:
                logger.error("ensure_indexes(%s.%s) error: %s", collection_name, model.document.get("name"), exc)


async def init_db(mongo_url: str, db_name: str):
    global _client, _db
    _client = AsyncMongoClient(mongo_url, serverSelectionTimeoutMS=8000)
    _db = _client[db_name]
    # One quick ping so a wrong MONGO_URL or blocked IP fails in seconds, not minutes.
    await _db.command("ping")
    await ensure_indexes(_db)
    return _db


async def close_db() -> None:
    global _client, _db
    if _client is not None:
        await _client.close()
        _client = None
        _db = None


def get_db():
    if _db is None:
        raise RuntimeError("Database not initialized. Ensure lifespan has run.")
    return _db


async def db_dependency():
    return get_db()
