# Auth Testing Playbook — AURELIA Interiors Admin

Single-admin password gate (bcrypt hash in MongoDB `users`, JWT httpOnly cookies).

## Setup
- ADMIN_EMAIL / ADMIN_PASSWORD from /app/backend/.env (seed only if `users` has no role=admin doc).
- JWT_SECRET from env; HS256; access 15 min / refresh 7 days; SameSite=None; Secure cookies.
- Brute force: `login_attempts` collection keyed by IP — 5 fails → 15 min lock.

## Steps
1. Mongo check:
   mongosh $DB_NAME --eval 'db.users.find({role:"admin"}).pretty()'
   → hash starts with $2b$
2. Login (preview host, cookies):
   curl -s -c /tmp/c.txt -X POST $API_URL/api/admin/login -H 'Content-Type: application/json' -d '{"password":"aurelia2026"}'
3. Me with cookies:
   curl -s -b /tmp/c.txt $API_URL/api/admin/me   → {"ok":true,...}
4. Protected CRUD: GET /api/admin/services with cookies → 200; without → 401.
5. Wrong password → 401 "Wrong password. Please try again." and increments lock counter.
6. Refresh: POST /api/admin/refresh with refresh cookie re-issues access token.
