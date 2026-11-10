# PRD — ANWESHAN Infra (formerly AURELIA Interiors)

> Rebranded 2026-11-05 with user's own logo artwork (arch+lamp mark, black/amber-gold) and name ANWESHAN INFRA · Interiors · Spaces · Lifestyle. Logo assets: /app/frontend/public/logo.png (mark) + logo-192.png (favicon).

## Original Problem Statement
"Act as a professional app developer and build a user friendly app for my customer about Interior designing. Build it accordingly so they can easily contact me and I also add new design idea on that app. Make it in section and very specific field that customer should not be confuse and a illiterate person also operate it."

User choices (from clarification round): English only; ALL contact channels (WhatsApp + Call + form); hidden admin page with password; show Homes, Shops and Furniture assessment; Warm & elegant look (cream/brown/gold); easy to find via Instagram/WhatsApp/mobile; very easy way for customers to select services whose prices the owner can edit later.

## User Personas
1. **Customer (any literacy level)** — wants to see work, pick a service, contact with ONE tap. Navigation is icon+label, big buttons, no jargon.
2. **Owner (studio admin)** — non-technical; needs to add design ideas (photo upload), edit service prices, read enquiries, update own contact details — all from a hidden /admin page.

## Architecture
- **Frontend**: React (CRA+craco), Tailwind, framer-motion (masked line-reveal hero, scroll reveals, layout animations), Lenis momentum scroll, sonner toasts, shadcn/ui. Warm editorial theme: cream #FDFBF7 / espresso #1A1412 / brass #C59B27; Playfair Display + Plus Jakarta Sans + JetBrains Mono.
- **Backend**: FastAPI (port 8001, /api prefix), MongoDB (motor). Models: Service, DesignIdea, Enquiry, SiteSettings (+users, files, login_attempts). JWT httpOnly cookie auth (15 min access / 7 d refresh, auto-refresh in frontend via adminApi). bcrypt password. Brute-force lockout (5 fails → 15 min).
- **Media**: Emergent object storage (EMERGENT_LLM_KEY + INTEGRATION_PROXY_URL); uploads via POST /api/admin/upload, served publicly via GET /api/files/{path}; DB file records soft-delete.
- **Routes**: / (one-page site) and /admin (hidden portal, footer link "Studio Login").

## Sections (public)
Hero (kinetic masked reveal, parallax bg, WhatsApp/Call CTAs, trust chips) → editorial marquee → Services (3 cards, prices from DB, enquire → prefilled WhatsApp) → Design Ideas gallery (filter All/Homes/Shops/Furniture, ask-about-this-design WhatsApp) → Furniture Assessment estimator (2 taps → rough range → send via WhatsApp) → How It Works (4 steps) → Contact (WhatsApp/Call/Instagram tiles + enquiry form → DB) → Footer. Mobile sticky bottom bar: Call + WhatsApp.

## Admin (/admin, password aurelia2026)
Design Ideas CRUD (photo upload or URL, category, description) · Services & Prices editor (price, timeline, show/hide, add/remove) · Enquiries viewer (call/WhatsApp reply, mark read, delete) · My Contact Info (phone, WhatsApp, Instagram, address, hours).

## Implemented (2026-11-05)
- Full backend with seeds (3 services, 7 ideas, settings, admin user), object-storage uploads, JWT auth + lockout.
- Full public site + admin portal as above; all data-testid attributes.
- Verified: curl suite (public GETs, enquiry POST, admin login/me/401s, price PUT, settings PUT, mark-read, refresh) + desktop/mobile/admin screenshots.

## Backlog (P0–P2)
- P0: New lead WhatsApp alert — backend hook is BUILT (notify_owner_whatsapp); awaiting Twilio keys (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_WHATSAPP_FROM) via secrets card. Also needs Twilio WhatsApp sender approval/sandbox.
- P1: More seed gallery items; owner to add real project photos via Admin → Add Idea (feature live).
- P1: WhatsApp click tracking / simple analytics.
- P2: Multi-image ideas; before/after slider; bilingual toggle if needed later.
