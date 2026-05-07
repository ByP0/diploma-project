import unittest

from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.cache.service import CacheService
from app.core.config import setting
from app.observability.security_middleware import SecurityHeadersMiddleware
from app.services.brute_force_service import brute_force_service


def build_request(path: str = "/api/auth/login", method: str = "POST") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("utf-8"),
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


class CacheAndSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def test_cache_service_roundtrip_and_prefix_delete(self) -> None:
        old_redis_enabled = setting.redis_enabled
        setting.redis_enabled = False
        try:
            cache = CacheService()
            await cache.set_json("test:cache:item", {"value": 42}, ttl_seconds=30)

            self.assertEqual(await cache.get_json("test:cache:item"), {"value": 42})

            await cache.delete_by_prefix("test:cache:")
            self.assertIsNone(await cache.get_json("test:cache:item"))
        finally:
            setting.redis_enabled = old_redis_enabled

    def test_brute_force_service_blocks_after_threshold(self) -> None:
        old_max_failures = setting.brute_force_max_failures
        old_window = setting.brute_force_window_seconds
        old_lockout = setting.brute_force_lockout_seconds
        try:
            setting.brute_force_max_failures = 2
            setting.brute_force_window_seconds = 60
            setting.brute_force_lockout_seconds = 60
            brute_force_service._entries.clear()
            brute_force_service._blocked_until.clear()
            request = build_request()

            brute_force_service.record_failure(email="buyer@example.com", request=request)
            brute_force_service.record_failure(email="buyer@example.com", request=request)

            with self.assertRaises(ValueError):
                brute_force_service.ensure_allowed(email="buyer@example.com", request=request)
        finally:
            setting.brute_force_max_failures = old_max_failures
            setting.brute_force_window_seconds = old_window
            setting.brute_force_lockout_seconds = old_lockout
            brute_force_service._entries.clear()
            brute_force_service._blocked_until.clear()

    async def test_docs_paths_use_docs_content_security_policy(self) -> None:
        middleware = SecurityHeadersMiddleware(app=lambda scope, receive, send: None)
        request = build_request("/docs", method="GET")

        async def call_next(_: Request) -> PlainTextResponse:
            return PlainTextResponse("ok")

        response = await middleware.dispatch(request, call_next)

        csp = response.headers["Content-Security-Policy"]
        self.assertEqual(csp, setting.security_docs_content_security_policy)
        self.assertIn("https://cdn.jsdelivr.net", csp)

    async def test_api_paths_use_default_content_security_policy(self) -> None:
        middleware = SecurityHeadersMiddleware(app=lambda scope, receive, send: None)
        request = build_request("/api/products", method="GET")

        async def call_next(_: Request) -> PlainTextResponse:
            return PlainTextResponse("ok")

        response = await middleware.dispatch(request, call_next)

        self.assertEqual(
            response.headers["Content-Security-Policy"],
            setting.security_content_security_policy,
        )
