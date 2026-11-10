import contextlib

import anyio
import boto3
from botocore.exceptions import ClientError

from app.storage.base import Storage


class R2Storage(Storage):
    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
    ):
        self.bucket = bucket
        self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def _sync_save(self, path: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=path,
            Body=data,
            ContentType=content_type,
        )

    def _sync_open(self, path: str) -> tuple[bytes, str]:
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=path)
            data = resp["Body"].read()
            content_type = resp.get("ContentType", "application/octet-stream")
            return data, content_type
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ("NoSuchKey", "404"):
                raise FileNotFoundError(f"R2 key not found: {path}") from exc
            raise

    def _sync_delete(self, path: str) -> None:
        with contextlib.suppress(ClientError):
            self.client.delete_object(Bucket=self.bucket, Key=path)

    async def save(self, path: str, data: bytes, content_type: str) -> None:
        await anyio.to_thread.run_sync(self._sync_save, path, data, content_type)

    async def open(self, path: str) -> tuple[bytes, str]:
        return await anyio.to_thread.run_sync(self._sync_open, path)

    async def delete(self, path: str) -> None:
        await anyio.to_thread.run_sync(self._sync_delete, path)
