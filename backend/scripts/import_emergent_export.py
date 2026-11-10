#!/usr/bin/env python3
"""CLI utility to import an Emergent data export into the ANWESHAN Infra database and storage."""

import asyncio
import mimetypes
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from bson import json_util
from pymongo import AsyncMongoClient

from app.config import get_settings
from app.storage import get_storage


def _infer_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


async def import_export(folder_path: Path) -> None:
    if not folder_path.is_dir():
        print(f"Error: Folder '{folder_path}' does not exist.")
        sys.exit(1)

    settings = get_settings()
    client = AsyncMongoClient(settings.MONGO_URL)
    db = client[settings.DB_NAME]
    storage = get_storage(settings)

    print(f"--- Importing Emergent export from: {folder_path.resolve()} ---")
    print(f"Target Database: {settings.DB_NAME}")
    print(f"Storage Backend: {settings.STORAGE_BACKEND}")
    print("---------------------------------------------------------------")

    # 1. Document Collections Mapping
    file_to_collection = {
        "services.json": "services",
        "ideas.json": "ideas",
        "enquiries.json": "enquiries",
        "settings.json": "settings",
        "files.json": "files",
    }

    counts = {}

    for filename, collection_name in file_to_collection.items():
        file_path = folder_path / filename
        if not file_path.is_file():
            print(f"Notice: {filename} not found, skipping collection '{collection_name}'.")
            continue

        raw_content = file_path.read_text(encoding="utf-8")
        try:
            docs = json_util.loads(raw_content)
        except Exception as exc:
            print(f"Error parsing JSON in {filename}: {exc}")
            continue

        if isinstance(docs, dict):
            docs = [docs]

        upserted = 0
        for doc in docs:
            # Never overwrite MongoDB _id
            doc.pop("_id", None)

            doc_id = doc.get("id")
            if not doc_id and collection_name == "settings":
                doc_id = "site"
                doc["id"] = "site"

            if doc_id:
                await db[collection_name].replace_one({"id": doc_id}, doc, upsert=True)
                upserted += 1

        counts[collection_name] = upserted
        print(f"Collection '{collection_name}': {upserted} documents upserted.")

    # 2. Copy Images into Storage
    images_dir = folder_path / "images"
    imported_images = 0

    if images_dir.is_dir():
        for img_file in images_dir.rglob("*"):
            if img_file.is_file():
                rel_path = img_file.relative_to(images_dir).as_posix()
                content_type = _infer_content_type(img_file.name)
                data = img_file.read_bytes()
                await storage.save(rel_path, data, content_type)
                imported_images += 1
        print(f"Images: {imported_images} files imported into storage.")
    else:
        print("Notice: 'images' directory not found in export.")

    # 3. Check for Missing Images Referenced in DB
    referenced_images = set()
    async for idea in db.ideas.find({}, {"image": 1}):
        img = idea.get("image")
        if img and not img.startswith("http"):
            referenced_images.add(img)

    async for f in db.files.find({"is_deleted": False}, {"storage_path": 1}):
        sp = f.get("storage_path")
        if sp:
            referenced_images.add(sp)

    missing_images = []
    for ref in referenced_images:
        try:
            await storage.open(ref)
        except Exception:
            missing_images.append(ref)

    print("---------------------------------------------------------------")
    print("MIGRATION SUMMARY:")
    for coll, count in counts.items():
        print(f"  • {coll}: {count} records")
    print(f"  • Images stored: {imported_images}")
    if missing_images:
        print(f"  • Warning: {len(missing_images)} referenced image(s) missing from storage:")
        for m in missing_images[:10]:
            print(f"      - {m}")
        if len(missing_images) > 10:
            print(f"      ... and {len(missing_images) - 10} more.")
    else:
        print("  • All referenced images successfully verified in storage.")
    print("Import completed safely (users collection was untouched).")

    await client.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_emergent_export.py <export_folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    asyncio.run(import_export(folder))


if __name__ == "__main__":
    main()
