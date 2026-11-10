"""Request body size limits, enforced before FastAPI parses the body.

FastAPI reads a whole multipart form (or JSON body) into memory before it runs
dependencies such as the admin login check, so without this an anonymous caller
could make the server buffer very large requests.
"""

import json

UPLOAD_PATH = "/api/admin/upload"
UPLOAD_LIMIT = 9 * 1024 * 1024  # 8 MB photo + multipart overhead
DEFAULT_LIMIT = 64 * 1024  # JSON bodies (enquiry form, admin edits) are tiny


class _TooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return

        is_upload = scope["path"].rstrip("/") == UPLOAD_PATH
        limit = UPLOAD_LIMIT if is_upload else DEFAULT_LIMIT
        message = (
            "Photo is too big. Please choose a photo under 8 MB."
            if is_upload
            else "Request is too large."
        )

        content_length = dict(scope.get("headers") or []).get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > limit:
                    await self._reject(send, message)
                    return
            except ValueError:
                await self._reject(send, "Invalid Content-Length.", status=400)
                return

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            msg = await receive()
            if msg["type"] == "http.request":
                received += len(msg.get("body", b""))
                if received > limit:
                    raise _TooLarge()
            return msg

        async def tracking_send(msg):
            nonlocal response_started
            if msg["type"] == "http.response.start":
                response_started = True
            await send(msg)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _TooLarge:
            if not response_started:
                await self._reject(send, message)

    @staticmethod
    async def _reject(send, detail: str, status: int = 413):
        body = json.dumps({"detail": detail}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
