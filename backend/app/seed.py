import logging
from datetime import UTC, datetime

from app.models import DesignIdea, Service, SiteSettings, User

logger = logging.getLogger("anweshan.seed")

SEED_SERVICES = [
    {
        "title": "Full Home Interiors",
        "description": "Every room designed and built for you — living room, kitchen, bedrooms and bathrooms. You approve the 3D design first, we handle the rest.",
        "price": "₹1,80,000 onwards",
        "timeline": "45–90 days",
        "icon": "home",
        "image": "https://images.unsplash.com/photo-1632120377007-c2adc3017b1e?crop=entropy&cs=srgb&fm=jpg&q=85",
        "sort_order": 1,
    },
    {
        "title": "Shop & Retail Interiors",
        "description": "Boutique stores, cafés, salons and offices that pull customers in and make them stay longer.",
        "price": "₹2,50,000 onwards",
        "timeline": "30–60 days",
        "icon": "shop",
        "image": "https://images.unsplash.com/photo-1551887196-72e32bfc7bf3?crop=entropy&cs=srgb&fm=jpg&q=85",
        "sort_order": 2,
    },
    {
        "title": "Furniture Assessment",
        "description": "We visit your home, check your furniture and woodwork, and tell you honestly what to repair, polish or remake.",
        "price": "Free first visit",
        "timeline": "1 day",
        "icon": "armchair",
        "image": "https://images.unsplash.com/photo-1768144092684-c1a5dd6c7aad?crop=entropy&cs=srgb&fm=jpg&q=85",
        "sort_order": 3,
    },
]

SEED_IDEAS = [
    {
        "title": "Warm Cream Living Room",
        "category": "homes",
        "description": "Soft creams, brass lamps and a statement arch — a living room that feels calm and expensive.",
        "image": "https://images.unsplash.com/photo-1632120377007-c2adc3017b1e?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
    {
        "title": "Classic Arch Nook",
        "category": "homes",
        "description": "Dark wood panelling, warm lighting and a cosy reading corner.",
        "image": "https://images.unsplash.com/photo-1700226034367-2fb120f48dfa?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
    {
        "title": "Modern Minimal Lounge",
        "category": "homes",
        "description": "Clean lines, muted tones and layered textures for a restful space.",
        "image": "https://images.unsplash.com/photo-1758915753451-b478b4e6f920?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
    {
        "title": "Boutique Café with Plants",
        "category": "shops",
        "description": "Hanging greens, warm bulbs and a counter built to be photographed.",
        "image": "https://images.unsplash.com/photo-1551887196-72e32bfc7bf3?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
    {
        "title": "Bakery & Café Counter",
        "category": "shops",
        "description": "Fresh green tiles, open display and a flow that keeps queues moving.",
        "image": "https://images.unsplash.com/photo-1601205741712-b261aff33a7d?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
    {
        "title": "Handcrafted Wood Chair",
        "category": "furniture",
        "description": "Solid wood, hand-finished — assess, polish or remake, we tell you honestly.",
        "image": "https://images.unsplash.com/photo-1768144092684-c1a5dd6c7aad?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
    {
        "title": "Sculpted Comfort Seat",
        "category": "furniture",
        "description": "Comfort-first curves in warm upholstery.",
        "image": "https://images.unsplash.com/photo-1762545078318-8443881c2d83?crop=entropy&cs=srgb&fm=jpg&q=85",
    },
]


async def seed_data(db, settings, hash_password_func) -> None:
    if await db.users.find_one({"role": "admin"}) is None:
        admin = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password_func(settings.ADMIN_PASSWORD),
            role="admin",
            token_version=1,
            created_at=datetime.now(UTC).isoformat(),
        )
        await db.users.insert_one(admin.to_mongo())
        logger.info("Seeded initial admin user: %s", settings.ADMIN_EMAIL)

    if await db.settings.find_one({"id": "site"}) is None:
        await db.settings.insert_one(
            SiteSettings(
                phone="+91 86584 29239",
                whatsapp="+91 86584 29239",
                instagram="https://www.instagram.com/anweshaninfra",
            ).to_mongo()
        )
        logger.info("Seeded initial site settings")

    # Demo services / ideas are added only ONCE, on a brand-new database.
    # Without this flag, deleting all demo content would bring it back on the
    # next restart.
    site = await db.settings.find_one({"id": "site"}) or {}
    if site.get("demo_content_seeded"):
        return

    has_content = (
        await db.services.count_documents({}) > 0 or await db.ideas.count_documents({}) > 0
    )
    if not has_content:
        for s in SEED_SERVICES:
            await db.services.insert_one(Service(**s).to_mongo())
        for i in SEED_IDEAS:
            await db.ideas.insert_one(DesignIdea(**i).to_mongo())
        logger.info("Seeded %d services and %d design ideas", len(SEED_SERVICES), len(SEED_IDEAS))

    await db.settings.update_one(
        {"id": "site"}, {"$set": {"demo_content_seeded": True}}, upsert=True
    )
