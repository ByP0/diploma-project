import unittest

from starlette.requests import Request

from app.observability.metrics import metrics_registry
from app.observability.rate_limit import rate_limiter


def build_request(path: str, method: str = "GET") -> Request:
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


class MetricsRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        metrics_registry.reset()

    def test_prometheus_render_contains_recorded_metrics(self) -> None:
        metrics_registry.record_http_request(
            method="GET",
            path="/api/orders",
            status_code=200,
            duration_ms=12.5,
        )
        metrics_registry.increment(
            "shop_admin_audit_events_total",
            action="update",
            resource_type="order",
        )

        rendered = metrics_registry.render_prometheus()

        self.assertIn("shop_http_requests_total", rendered)
        self.assertIn('path="/api/orders"', rendered)
        self.assertIn("shop_admin_audit_events_total", rendered)


class RateLimiterTests(unittest.TestCase):
    def setUp(self) -> None:
        rate_limiter.reset()

    def test_auth_policy_eventually_rejects_requests(self) -> None:
        request = build_request("/api/auth/login", method="POST")
        allowed = []
        for _ in range(21):
            allowed.append(rate_limiter.check(request)[0])

        self.assertTrue(all(allowed[:-1]))
        self.assertFalse(allowed[-1])
