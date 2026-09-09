"""Bound raw bytes before JSON parsing, including chunked requests."""
from starlette.responses import JSONResponse

MAX_BATCH_BYTES = 10 * 1024 * 1024


class BatchBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"].rstrip("/") != "/api/v1/tasks/batch":
            return await self.app(scope, receive, send)
        chunks = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(chunks) + len(chunk) > MAX_BATCH_BYTES:
                response = JSONResponse({"status": "error", "error": {"code": "request_too_large", "message": "Request exceeds 10 MiB"}}, status_code=413)
                return await response(scope, receive, send)
            chunks.extend(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(chunks), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)
