from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    async def save(self, path: str, data: bytes, content_type: str) -> None:
        """Persist object data at the given path."""

    @abstractmethod
    async def open(self, path: str) -> tuple[bytes, str]:
        """Retrieve object bytes and content_type by path. Raise FileNotFoundError if not found."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove object at path if it exists."""
