# ANWESHAN Infra — Backend Documentation

This is the standalone, production-ready backend for the **ANWESHAN Infra** interior design studio website. It is built with **FastAPI**, native **Async PyMongo** (`AsyncMongoClient`), and modular storage (Local disk or Cloudflare R2). It has **zero Emergent platform dependencies** and runs anywhere — on your local Windows PC or on free cloud hosting.

---

## 1. Quick Local Setup (Windows-First)

### Step 1: Prerequisites
1. **Python 3.12** (or 3.11+):
   - Check with `python --version`.
2. **MongoDB Community Server** (Local) OR a free **MongoDB Atlas M0** cluster:
   - To install MongoDB locally on Windows: Download [MongoDB Community Server](https://www.mongodb.com/try/download/community) and run the installer. Ensure "Install MongoDB as a Service" is checked.
   - Verify it is running in PowerShell:
     ```powershell
     Get-Service *mongo*
     ```
     Status should show `Running`.

### Step 2: Create Virtual Environment
Open PowerShell, navigate to the `backend` folder, and create the virtual environment:
```powershell
cd backend
python -m venv .venv
```

Activate the environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
Install production and development dependencies:
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Generate a secure 32+ character JWT secret:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Open `.env` in your editor and configure:
- `MONGO_URL`: `mongodb://localhost:27017` (or your MongoDB Atlas connection string)
- `DB_NAME`: `anweshan_infra`
- `JWT_SECRET`: Paste the generated secret key (must be at least 32 characters)
- `ADMIN_PASSWORD`: Your desired initial administrator password (only used during initial seeding)
- `STORAGE_BACKEND`: `local` (files are stored in `backend/uploads`)

*(Note: Never commit `.env` to Git. It is excluded by `.gitignore`.)*

---

## 2. Running the Server

Start the backend server on port 8001:
```powershell
uvicorn server:app --reload --port 8001
```

Or from the project root:
```powershell
$env:PYTHONPATH="backend"; backend\.venv\Scripts\uvicorn.exe server:app --reload --port 8001
```

Verify it is running by checking the health endpoints:
- Liveness check: `http://localhost:8001/api/health`
- Database readiness check: `http://localhost:8001/api/ready`
- Interactive API Docs (disabled when `ENV=prod`): `http://localhost:8001/docs`

---

## 3. Running Automated Tests

The automated test suite runs 27 comprehensive tests against a real MongoDB test database (`anweshan_test`, which is automatically dropped after the run) and a temporary upload directory:

```powershell
backend\.venv\Scripts\pytest -v
```

To run code quality and linting checks:
```powershell
backend\.venv\Scripts\ruff.exe check backend tests
```

---

## 4. Admin Management Scripts

### Resetting Admin Password
To reset or change the studio administrator password directly from the terminal:
```powershell
backend\.venv\Scripts\python scripts/set_admin_password.py "YourNewStrongPassword123"
```
*(This updates the bcrypt hash and atomically increments `token_version`, instantly logging out all active sessions across all devices.)*

### Importing Emergent Data Export
When you receive your data export from Emergent (containing `services.json`, `ideas.json`, `enquiries.json`, `settings.json`, `files.json`, and `images/`):
```powershell
backend\.venv\Scripts\python scripts/import_emergent_export.py path/to/emergent_export
```
- Upserts every record by its unique `id` (safe to run multiple times without duplicating data).
- Copies all images into the configured storage at the same relative paths so existing image URLs keep working.
- Leaves the `users` collection completely untouched.

---

## 5. Security Architecture

1. **Authentication**: Password-only login with `bcrypt` (5.0.0, rejecting passwords >72 bytes with a friendly 400). Issues two `httpOnly` cookies:
   - `access_token` (15 min lifespan)
   - `refresh_token` (7 days lifespan)
2. **Session Revocation**: Every user document stores `token_version: int`. JWT payloads include `ver: token_version`. Both `/api/admin/logout` and `/api/admin/password` increment `token_version`, immediately invalidating all previously issued tokens.
3. **CSRF & Origin Defense**: All state-changing `/api/admin/*` routes reject requests if `Sec-Fetch-Site: cross-site` or if the `Origin` header does not match `CORS_ORIGINS`.
4. **Brute-Force Lockout**: 5 failed login attempts within 15 minutes lock the client IP for 15 minutes with HTTP 429 using an atomic MongoDB update and TTL index.
5. **Upload Verification**: Files are streamed with an 8 MB hard limit, inspected with Pillow (rejecting fake extensions or decompression bombs), auto-rotated, resized so the longest dimension <= 2000px, and stripped of all EXIF/GPS metadata.
6. **Path Traversal Protection**: Local storage strictly resolves paths and asserts `target.relative_to(upload_dir)`, returning 404 for any directory traversal attempt.
7. **Lead Notifications**: Dispatched via FastAPI `BackgroundTask` (supporting Telegram Bot, Resend Email, and Twilio WhatsApp) so notification failures never delay or disrupt customer enquiries.

---

## 6. Production Reverse Proxy Note

In production behind reverse proxies (Render, Koyeb, Nginx, Cloudflare), run uvicorn with:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --proxy-headers --forwarded-allow-ips="<PROXY_IP>"
```
*(Never set `--forwarded-allow-ips="*"` in production to prevent IP spoofing.)*
