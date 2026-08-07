from __future__ import annotations

import time

from fastapi import HTTPException, status
from redis import Redis
from redis.exceptions import RedisError

from app.config import get_settings


class RateLimiter:
    def __init__(self, redis_url: str) -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True, socket_timeout=2)

    def check(self, bucket: str, identifier: str, limit: int) -> None:
        window = int(time.time() // 60)
        key = f"ccn-rate:{bucket}:{identifier}:{window}"
        block_key = f"ccn-rate:block:{bucket}:{identifier}"
        try:
            if self.client.exists(block_key):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"code": "rate_limit_exceeded", "message": "Too many requests"},
                    headers={"Retry-After": "900"},
                )
            count = self.client.incr(key)
            if count == 1:
                self.client.expire(key, 120)
        except RedisError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "rate_limiter_unavailable", "message": "Service temporarily unavailable"},
            ) from exc
        if count > limit:
            retry_after = "60"
            if bucket == "auth-failure":
                retry_after = "900"
                try:
                    self.client.setex(block_key, 900, "1")
                except RedisError:
                    pass
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "rate_limit_exceeded", "message": "Too many requests"},
                headers={"Retry-After": retry_after},
            )


_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter(get_settings().redis_url)
    return _limiter
