from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    metric_type: str
    help_text: str


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counter_definitions: dict[str, MetricDefinition] = {}
        self._summary_definitions: dict[str, MetricDefinition] = {}
        self._counters: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(
            lambda: defaultdict(float)
        )
        self._summaries: dict[str, dict[tuple[tuple[str, str], ...], dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: {"count": 0.0, "sum": 0.0})
        )

    @staticmethod
    def _normalize_labels(labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted((key, str(value)) for key, value in labels.items()))

    def register_counter(self, name: str, help_text: str) -> None:
        self._counter_definitions.setdefault(
            name,
            MetricDefinition(name=name, metric_type="counter", help_text=help_text),
        )

    def register_summary(self, name: str, help_text: str) -> None:
        self._summary_definitions.setdefault(
            name,
            MetricDefinition(name=name, metric_type="summary", help_text=help_text),
        )

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        self.register_counter(name, f"Counter {name}")
        key = self._normalize_labels(labels)
        with self._lock:
            self._counters[name][key] += value

    def observe(self, name: str, value: float, **labels: str) -> None:
        self.register_summary(name, f"Summary {name}")
        key = self._normalize_labels(labels)
        with self._lock:
            self._summaries[name][key]["count"] += 1
            self._summaries[name][key]["sum"] += value

    def record_http_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        self.register_counter(
            "shop_http_requests_total",
            "Total number of HTTP requests",
        )
        self.register_summary(
            "shop_http_request_duration_ms",
            "HTTP request duration in milliseconds",
        )
        self.increment(
            "shop_http_requests_total",
            method=method,
            path=path,
            status=str(status_code),
        )
        self.observe(
            "shop_http_request_duration_ms",
            duration_ms,
            method=method,
            path=path,
        )

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            for definition in self._counter_definitions.values():
                lines.append(f"# HELP {definition.name} {definition.help_text}")
                lines.append(f"# TYPE {definition.name} {definition.metric_type}")
                for labels, value in self._counters[definition.name].items():
                    lines.append(self._render_sample(definition.name, value, labels))

            for definition in self._summary_definitions.values():
                lines.append(f"# HELP {definition.name} {definition.help_text}")
                lines.append(f"# TYPE {definition.name} {definition.metric_type}")
                for labels, values in self._summaries[definition.name].items():
                    lines.append(
                        self._render_sample(f"{definition.name}_count", values["count"], labels)
                    )
                    lines.append(
                        self._render_sample(f"{definition.name}_sum", values["sum"], labels)
                    )

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._counter_definitions.clear()
            self._summary_definitions.clear()
            self._counters.clear()
            self._summaries.clear()

    @staticmethod
    def _render_sample(
        name: str,
        value: float,
        labels: tuple[tuple[str, str], ...],
    ) -> str:
        if not labels:
            return f"{name} {value}"
        labels_text = ",".join(f'{key}="{val}"' for key, val in labels)
        return f"{name}{{{labels_text}}} {value}"


metrics_registry = MetricsRegistry()
