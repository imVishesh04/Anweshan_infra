#!/usr/bin/env python3
"""CLI utility to reset the ANWESHAN Infra admin password from the terminal."""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from datetime import UTC

from pymongo import AsyncMongoClient

from app.config import get_settings
from app.security import hash_password


async def set_admin_password(new_password: str) -> None:
    settings = get_settings()

    if len(new_password) < 8:
        print("Error: Password must be at least 8 characters long.")
        sys.exit(1)

    pw_bytes = new_password.encode("utf-8")
    if len(pw_bytes) > 72:
        print("Error: Password cannot exceed 72 characters.")
        sys.exit(1)

    client = AsyncMongoClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]

    new_hash = hash_password(new_password)
    admin = await db.users.find_one({"role": "admin"})

    if admin:
        new_version = admin.get("token_version", 1) + 1
        await db.users.update_one(
            {"role": "admin"},
            {
                "$set": {
                    "password_hash": new_hash,
                    "token_version": new_version,
                }
            },
        )
        print(f"Successfully updated admin password for {admin.get('email', 'admin')}.")
        print("All existing active sessions have been invalidated.")
    else:
        import uuid
        from datetime import datetime
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": settings.ADMIN_EMAIL,
            "password_hash": new_hash,
            "role": "admin",
            "token_version": 1,
            "created_at": datetime.now(UTC).isoformat(),
        })
        print(f"Created new admin user with email {settings.ADMIN_EMAIL}.")

    await client.close()


def main():
    if len(sys.argv) > 1:
        pwd = sys.argv[1].strip()
    else:
        import getpass
        pwd = getpass.getpass("Enter new admin password: ").strip()

    if not pwd:
        print("Error: Password cannot be empty.")
        sys.exit(1)

    asyncio.run(set_admin_password(pwd))


if __name__ == "__main__":
    main()
