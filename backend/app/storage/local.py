import mimetypes
from pathlib import Path

import anyio

from app.storage.base import Storage


def _infer_content_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


class LocalStorage(Storage):
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir.resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, rel_path: str) -> Path:
        clean = rel_path.strip().lstrip("/\\")
        target = (self.base_dir / clean).resolve()
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            raise PermissionError(f"Path traversal detected: {rel_path}")
        return target

    def _sync_save(self, target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def _sync_open(self, target: Path) -> tuple[bytes, str]:
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {target}")
        data = target.read_bytes()
        content_type = _infer_content_type(target)
        return data, content_type

    def _sync_delete(self, target: Path) -> None:
        if target.is_file():
            target.unlink()

    async def save(self, path: str, data: bytes, content_type: str) -> None:
        target = self._resolve_safe_path(path)
        await anyio.to_thread.run_sync(self._sync_save, target, data)

    async def open(self, path: str) -> tuple[bytes, str]:
        try:
            target = self._resolve_safe_path(path)
        except PermissionError:
            raise FileNotFoundError(f"File not found or invalid: {path}")
        return await anyio.to_thread.run_sync(self._sync_open, target)

    async def delete(self, path: str) -> None:
        try:
            target = self._resolve_safe_path(path)
            await anyio.to_thread.run_sync(self._sync_delete, target)
        except (PermissionError, FileNotFoundError):
            pass
