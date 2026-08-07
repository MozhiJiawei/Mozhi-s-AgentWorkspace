from __future__ import annotations

from fastapi import HTTPException
import pytest

from app.rate_limit.service import RateLimiter


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int | str] = {}

    def exists(self, key: str) -> bool:
        return key in self.values

    def incr(self, key: str) -> int:
        value = int(self.values.get(key, 0)) + 1
        self.values[key] = value
        return value

    def expire(self, _key: str, _seconds: int) -> None:
        return None

    def setex(self, key: str, _seconds: int, value: str) -> None:
        self.values[key] = value


def test_auth_failures_create_a_temporary_block():
    limiter = RateLimiter.__new__(RateLimiter)
    limiter.client = FakeRedis()
    for _ in range(2):
        limiter.check("auth-failure", "127.0.0.1", 2)
    with pytest.raises(HTTPException) as exceeded:
        limiter.check("auth-failure", "127.0.0.1", 2)
    assert exceeded.value.status_code == 429
    assert exceeded.value.headers["Retry-After"] == "900"
    with pytest.raises(HTTPException):
        limiter.check("auth-failure", "127.0.0.1", 2)
