# ANWESHAN Infra — Live karne ki simple guide

## Kaun kahan rahega
- **anweshaninfra.in** → **Netlify** (website — free)
- **api.anweshaninfra.in** → **Railway** (backend — ~$5/month)
- **MongoDB Atlas** → database (free)
- **Cloudflare R2** → photos (free)
- **Telegram bot** → naye customer ka alert (free)

Customer sirf `anweshaninfra.in` kholega. Netlify chupke se `/api` wali requests Railway ko bhej dega.

---

## Step 0 — Code GitHub par daalo (private repo)
1. github.com par **New repository** banao → naam `anweshan-infra` → **Private**.
2. Project folder me terminal:
   ```
   git add -A
   git commit -m "deploy ready"
   git remote add origin https://github.com/<aapka-username>/anweshan-infra.git
   git push -u origin main
   ```
   (Agar branch ka naam `master` hai to `main` ki jagah `master` likho.)
3. GitHub par check karo: **`.env` file wahan NAHI dikhni chahiye.**

## Step 1 — MongoDB Atlas (database)
1. mongodb.com/atlas → free account → **Create cluster** → **M0 Free** → AWS → **Mumbai**.
2. **Database Access** → user banao (jaise `anweshan_admin`) + strong password (note kar lo).
3. **Network Access** → `0.0.0.0/0` add karo.
4. **Connect → Drivers** → connection string copy karo, `<password>` ki jagah apna password daalo.

## Step 2 — Cloudflare R2 (photos)
1. dash.cloudflare.com → **R2** → **Create bucket** → naam `anweshan-media`.
2. **Manage API Tokens** → **Create API token** → permission **Object Read & Write** → bucket `anweshan-media`.
3. Note karo: **Account ID, Access Key ID, Secret Access Key**.

## Step 3 — Telegram alert bot
1. Telegram me **@BotFather** → `/newbot` → naam do → **token** milega.
2. Owner ke phone se apne naye bot ko `/start` bhejo.
3. Browser me kholo: `https://api.telegram.org/bot<TOKEN>/getUpdates` → `"chat":{"id": ... }` wala number = **chat id**.

## Step 4 — Railway (backend)
1. railway.com → login with GitHub → **Hobby plan** lo.
2. **New Project → Deploy from GitHub repo** → `anweshan-infra` chuno.
3. Service → **Settings**:
   - **Root Directory**: `backend`
   - **Custom Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Healthcheck Path**: `/api/health`
4. Service → **Variables** → ye sab daalo (Raw Editor me paste kar sakte ho):
   ```
   ENV=prod
   MONGO_URL=<Atlas connection string>
   DB_NAME=anweshan_infra
   JWT_SECRET=<naya random — neeche command se banao>
   ADMIN_PASSWORD=<naya strong admin password>
   ADMIN_EMAIL=admin@anweshaninfra.in
   CORS_ORIGINS=https://anweshaninfra.in,https://www.anweshaninfra.in
   COOKIE_SECURE=true
   COOKIE_SAMESITE=lax
   FORWARDED_ALLOW_IPS=*
   STORAGE_BACKEND=r2
   R2_ACCOUNT_ID=<...>
   R2_ACCESS_KEY_ID=<...>
   R2_SECRET_ACCESS_KEY=<...>
   R2_BUCKET=anweshan-media
   NOTIFY_TELEGRAM_BOT_TOKEN=<...>
   NOTIFY_TELEGRAM_CHAT_ID=<...>
   ```
   JWT_SECRET banane ke liye laptop par: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
5. Deploy hone do. **Settings → Networking → Custom Domain** → `api.anweshaninfra.in` likho → Railway **2 records** dikhayega (CNAME + TXT). Unhe Step 6 me GoDaddy me daalna hai.

## Step 5 — Netlify (website)
1. netlify.com → login with GitHub → **Add new project → Import from GitHub** → `anweshan-infra`.
2. **Base directory**: `frontend` (baaki sab `netlify.toml` khud set kar dega) → **Deploy**.
3. **Domain management → Add a domain** → `anweshaninfra.in` (www bhi add ho jayega).

## Step 6 — GoDaddy DNS (domain jodna)
GoDaddy → My Products → `anweshaninfra.in` → **DNS** → **Manage DNS**:

| Type | Name | Value | Kiske liye |
|---|---|---|---|
| A | `@` | `75.2.60.5` | website (Netlify) |
| CNAME | `www` | `<aapki-site>.netlify.app` | website www (Netlify) |
| CNAME | `api` | Railway jo dikhaye (`xxxx.up.railway.app`) | backend (Railway) |
| TXT | `_railway-verify.api` | Railway jo dikhaye | Railway verification |

- `@` wala purana **"Parked"** A record **delete** karo, warna GoDaddy ka page khulta rahega.
- Records lagne me 10 min se 24 ghante lag sakte hain. HTTPS (lock) Netlify aur Railway khud de dete hain.

## Step 7 — Purana Emergent data daalna (ek baar)
Laptop par `backend/.env` me **temporarily** Atlas wala `MONGO_URL`, `DB_NAME=anweshan_infra`, `STORAGE_BACKEND=r2` aur R2 keys daalo, phir:
```
cd backend
.venv\Scripts\Activate.ps1
python scripts/import_emergent_export.py ..\emergent_export
```
Baad me `.env` wapas local wale settings par kar do.

## Step 8 — Final check
- `https://api.anweshaninfra.in/api/health` → `{"status":"ok"}`
- `https://anweshaninfra.in` → website khule, photos dikhein
- Phone se enquiry bhejo → Telegram par alert aaye
- `https://anweshaninfra.in/admin` → login → photo upload → home page par dikhe
- iPhone/Safari par bhi admin login try karo

## Kuch galat ho to
- **Admin login "Origin not allowed"** → Railway me `CORS_ORIGINS` me exact domain check karo (https, bina `/` ke).
- **Website khule par data na aaye** → `api.anweshaninfra.in` abhi verify nahi hua; Railway me green tick ka wait karo.
- **Railway deploy crash "STORAGE_BACKEND=r2 but ..."** → R2 ki koi variable missing hai.
- **Admin password bhool gaye** → laptop se Atlas `MONGO_URL` ke saath `python scripts/set_admin_password.py <naya-password>`.
