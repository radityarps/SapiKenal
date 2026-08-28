"""ASGI guard that hides benchmark-only routes unless explicitly enabled."""

from collections.abc import Awaitable, Callable
from typing import Any

from config import settings

BENCHMARK_PATH_PREFIX = "/api/benchmark"

Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]


class BenchmarkEndpointGuardMiddleware:
    """Reject HTTP and WebSocket benchmark traffic before FastAPI parses a body."""

    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request_type = scope["type"]
        path = scope.get("path", "")
        is_benchmark_request = path == BENCHMARK_PATH_PREFIX or path.startswith(
            f"{BENCHMARK_PATH_PREFIX}/"
        )
        if not is_benchmark_request or settings.benchmark_enabled:
            await self.app(scope, receive, send)
            return

        if request_type == "http":
            body = b'{"detail":"Not Found"}'
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
        elif request_type == "websocket":
            await send({"type": "websocket.close", "code": 1008})
        else:
            await self.app(scope, receive, send)
