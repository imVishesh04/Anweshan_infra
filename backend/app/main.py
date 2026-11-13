import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import close_db, init_db
from app.limits import BodySizeLimitMiddleware
from app.routers import admin_auth_router, admin_content_router, public_router, whatsapp_router
from app.security import hash_password
from app.seed import seed_data
from app.storage import get_storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# httpx logs every request URL at INFO level. The Telegram URL contains the bot
# token, so these loggers must stay quiet.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("anweshan.main")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disallow caching for all admin routes
        if request.url.path.startswith("/api/admin"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting ANWESHAN Infra Backend (ENV=%s)...", settings.ENV)

    # 1. Initialize MongoDB connection & ensure indexes
    db = await init_db(settings.MONGO_URL, settings.DB_NAME)
    logger.info("Connected to MongoDB (%s)", settings.DB_NAME)

    # 2. Seed initial data (admin, site settings, services, ideas)
    await seed_data(db, settings, hash_password)

    # 3. Initialize storage subsystem
    get_storage(settings)

    yield

    # 4. Graceful shutdown
    logger.info("Shutting down database connection...")
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    is_prod = settings.ENV.lower() == "prod"

    app = FastAPI(
        title="ANWESHAN Infra API",
        version="2.0.0",
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration (explicit origins, remove legacy emergent regex)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Reject oversized request bodies before anything reads them into memory
    app.add_middleware(BodySizeLimitMiddleware)

    # Routers
    app.include_router(public_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_content_router)
    app.include_router(whatsapp_router)

    return app


app = create_app()
