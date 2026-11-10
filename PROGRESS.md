# ANWESHAN Infra Backend Modernization Progress

## Phase Tracking

- [x] **Phase 1: Plan + Questions**
  - Analyzed codebase, reviewed API contracts, identified bugs (category filter, etc.).
  - Produced detailed Implementation Plan artifact.
  - Approved by user. Initialized local git repository.

- [x] **Phase 2: Restructure into `app/`, config, lifespan, PyMongo async, requirements**
  - Created Python 3.12 virtualenv `backend/.venv` and installed all pinned requirements.
  - Implemented `app/config.py` (pydantic-settings, validating `JWT_SECRET` length >= 32).
  - Implemented `app/db.py` (native `AsyncMongoClient`, index creation, connection lifecycle).
  - Implemented `app/models.py` (Pydantic models with uuid4 string IDs, never exposing `_id`).
  - Implemented `app/seed.py` (idempotent seeding of 3 services, 7 ideas, site settings, admin).
  - Implemented `app/main.py` (FastAPI app factory, lifespan context manager, CORS without Emergent regex, security headers middleware).
  - Implemented `app/routers/public.py` (fixed category filter bug, added `/api/health` and `/api/ready`).
  - Created `backend/server.py` 2-line backward-compatible shim.
  - Created `backend/.env.example`.
  - Git commit: `ccceba9`.

- [x] **Phase 3: Storage abstraction + upload safety + file serving**
  - Implemented `app/storage/base.py` (`Storage` ABC: `save`, `open`, `delete`).
  - Implemented `app/storage/local.py` (strict path traversal defense ensuring path resolves within `UPLOAD_DIR`, offloaded via `anyio.to_thread.run_sync`).
  - Implemented `app/storage/r2.py` (Cloudflare R2 via boto3 S3 API, offloaded via `anyio.to_thread.run_sync`).
  - Implemented `app/storage/__init__.py` storage factory singleton.
  - Built streaming upload pipeline with 8 MB hard limit stop, Pillow image validation, decompression bomb limit, auto-rotation by EXIF, Lanczos resizing to max 2000px, clean re-encoding (stripping EXIF/GPS).
  - Configured file serving with `Cache-Control: public, max-age=31536000, immutable`, `X-Content-Type-Options: nosniff`.
  - Implemented legacy path support (e.g. `aurelia-interiors/uploads/...` served transparently if present, 404 if missing).
  - Implemented orphan image cleanup on idea deletion and image replacement.
  - Git commit: `82e6ab5`.

- [x] **Phase 4: Auth hardening, CSRF, rate limits, enquiry validation, notifier**
  - Integrated `bcrypt==5.0.0` with friendly 400 error on passwords >72 bytes.
  - Implemented `token_version` tracking in MongoDB `users` collection and in JWT claims (`ver`).
  - Hardened `require_admin` and `/api/admin/refresh` to check `token_version` against DB, invalidating sessions on logout or password change.
  - Implemented CSRF defense: rejecting `Sec-Fetch-Site: cross-site` and validating `Origin` against `CORS_ORIGINS`.
  - Built atomic brute-force login lockout (5 failed attempts within 15 min lock the IP with 429 via atomic `find_one_and_update` and TTL index).
  - Built enquiry input validation (name 2-80 chars, phone 10-13 digits, service <=100, message <=1000) with plain English error messages.
  - Built atomic enquiry rate limiting (max 5 per IP per 10 minutes -> 429).
  - Built pluggable lead notification subsystem (`app/notify.py`) supporting Telegram Bot, Resend Email, and Twilio WhatsApp with no hardcoded credentials, dispatched as a FastAPI `BackgroundTask`.
  - Added `PUT /api/admin/password` endpoint.
  - Git commit: `25d8ae4`.

- [x] **Phase 5: Frontend proxy changes, import script, seed check**
  - Updated `frontend/src/lib/api.js`: `export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";`.
  - Configured devServer proxy in `frontend/craco.config.js`: `/api` -> `http://localhost:8001` (webpack-dev-server v5 array format).
  - Created `frontend/.env.example` with instructions on legacy Emergent variables.
  - Built CLI password reset script: `backend/scripts/set_admin_password.py`.
  - Built idempotent Emergent export import script: `backend/scripts/import_emergent_export.py`.
  - Git commit: `7696c3b`.

- [x] **Phase 6: Tests + ruff until green; browser verification**
  - Implemented comprehensive 27-test automated pytest suite in `tests/` covering public routes, health/readiness, category filtering, enquiries, rate limits, auth lockout, token revocation, password change, CSRF defense, admin CRUD, file uploads, path traversal, legacy paths, and migration idempotency.
  - All 27 tests passing against real MongoDB test database (`anweshan_test`).
  - `ruff check backend tests` passing with 0 errors.
  - Ran automated live browser verification with Playwright across the entire user journey: homepage, gallery filtering, enquiry submission, admin login, idea addition with photo upload, homepage verification, service price editing, enquiry mark-read, and admin logout.
  - All 10 screenshots captured and saved to `test_reports/screenshots/` and artifact directory.
  - Git commit: `1476bc2`.

- [x] **Phase 7: README, DEPLOY.md, final Walkthrough**
  - Created `backend/README.md` with Windows-first developer guide and CLI reference.
  - Created `DEPLOY.md` with production deployment guide for MongoDB Atlas M0, Render/Koyeb, Cloudflare R2, and Vercel same-site proxying.
