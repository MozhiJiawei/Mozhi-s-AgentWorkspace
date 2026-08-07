from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.rate_limit.service import RateLimiter, get_rate_limiter


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    fingerprint: str


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def source_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def authenticate(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    settings: Settings = Depends(get_settings),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> Principal:
    token = credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else ""
    if token and settings.api_key and hmac.compare_digest(token, settings.api_key):
        principal = Principal(fingerprint=fingerprint(token))
        request.state.principal = principal
        return principal
    limiter.check("auth-failure", source_ip(request), settings.auth_fail_limit_per_minute)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": "Invalid credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_api_key(
    request: Request,
    principal: Principal = Depends(authenticate),
    settings: Settings = Depends(get_settings),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> Principal:
    is_read = request.method == "GET"
    limit = settings.read_limit_per_minute if is_read else settings.write_limit_per_minute
    limiter.check("read" if is_read else "write", principal.fingerprint, limit)
    return principal
