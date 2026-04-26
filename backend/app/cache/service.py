from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Protocol

from app.core.config import setting

try:  # pragma: no cover - optional dependency at runtime
    import redis.asyncio as redis_asyncio
except Exception:  # pragma: no cover - optional dependency at runtime
    redis_asyncio = None


class CacheBackend(Protocol):
    async def get(self, key: str) -> str | None:
        ...

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def delete_by_prefix(self, prefix: str) -> None:
        ...

    async def ping(self) -> bool:
        ...


class InMemoryCacheBackend:
    def __init__(self) -> None:
        self._entries: dict[str, tuple[datetime, str]] = {}
        self._lock = Lock()

    async def get(self, key: str) -> str | None:
        now = datetime.now(timezone.utc)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                self._entries.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(1, ttl_seconds))
        with self._lock:
            self._entries[key] = (expires_at, value)

    async def delete(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    async def delete_by_prefix(self, prefix: str) -> None:
        with self._lock:
            keys = [key for key in self._entries if key.startswith(prefix)]
            for key in keys:
                self._entries.pop(key, None)

    async def ping(self) -> bool:
        return True


class RedisCacheBackend:
    def __init__(self) -> None:
        if redis_asyncio is None:
            raise RuntimeError("redis is not installed")
        self._client = redis_asyncio.from_url(setting.redis_url, encoding="utf-8", decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        await self._client.set(name=key, value=value, ex=max(1, ttl_seconds))

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def delete_by_prefix(self, prefix: str) -> None:
        async for key in self._client.scan_iter(match=f"{prefix}*"):
            await self._client.delete(key)

    async def ping(self) -> bool:
        return bool(await self._client.ping())


class CacheService:
    def __init__(self) -> None:
        self._backend = self._build_backend()

    async def get_json(self, key: str) -> Any | None:
        raw_value = await self._backend.get(key)
        if raw_value is None:
            return None
        return json.loads(raw_value)

    async def set_json(
        self,
        key: str,
        value: Any,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        await self._backend.set(
            key,
            json.dumps(value, ensure_ascii=False, default=str),
            ttl_seconds or setting.redis_default_ttl_seconds,
        )

    async def delete(self, key: str) -> None:
        await self._backend.delete(key)

    async def delete_by_prefix(self, prefix: str) -> None:
        await self._backend.delete_by_prefix(prefix)

    async def ping(self) -> bool:
        return await self._backend.ping()

    @property
    def backend_name(self) -> str:
        return type(self._backend).__name__

    @staticmethod
    def _build_backend() -> CacheBackend:
        if setting.redis_enabled and redis_asyncio is not None:
            return RedisCacheBackend()
        return InMemoryCacheBackend()


cache_service = CacheService()
