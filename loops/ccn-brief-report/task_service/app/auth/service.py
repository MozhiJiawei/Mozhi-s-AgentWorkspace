from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import os
import time

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.rate_limit.service import RateLimiter, get_rate_limiter


bearer = HTTPBearer(auto_error=False)
DASHBOARD_SESSION_COOKIE = "ccn_dashboard_session"
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 600_000


@dataclass(frozen=True)
class Principal:
    fingerprint: str


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_dashboard_password(password: str, *, iterations: int = PASSWORD_HASH_ITERATIONS) -> str:
    if not password:
        raise ValueError("Dashboard password cannot be empty")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{PASSWORD_HASH_ALGORITHM}:{iterations}:{_encode(salt)}:{_encode(digest)}"


def verify_dashboard_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iteration_text, salt_text, digest_text = encoded_hash.split(":", 3)
        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False
        iterations = int(iteration_text)
        if not 100_000 <= iterations <= 10_000_000:
            return False
        expected = _decode(digest_text)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), _decode(salt_text), iterations
        )
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(actual, expected)


def _session_key(settings: Settings) -> bytes:
    material = f"ccn-dashboard-session:{settings.api_key}:{settings.dashboard_password_hash}"
    return hashlib.sha256(material.encode("utf-8")).digest()


def create_dashboard_session(settings: Settings, *, now: int | None = None) -> str:
    issued_at = int(time.time() if now is None else now)
    expires_at = issued_at + settings.dashboard_session_ttl_seconds
    message = f"v1.{expires_at}"
    signature = hmac.new(_session_key(settings), message.encode("ascii"), hashlib.sha256)
    return f"{message}.{_encode(signature.digest())}"


def verify_dashboard_session(value: str, settings: Settings, *, now: int | None = None) -> bool:
    if not value or not settings.dashboard_password_hash:
        return False
    try:
        version, expires_text, signature = value.split(".", 2)
        expires_at = int(expires_text)
    except (TypeError, ValueError):
        return False
    if version != "v1" or expires_at < int(time.time() if now is None else now):
        return False
    message = f"{version}.{expires_at}"
    expected = hmac.new(_session_key(settings), message.encode("ascii"), hashlib.sha256)
    return hmac.compare_digest(signature, _encode(expected.digest()))


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
    dashboard_session = request.cookies.get(DASHBOARD_SESSION_COOKIE, "")
    if verify_dashboard_session(dashboard_session, settings):
        principal = Principal(fingerprint="dashboard")
        request.state.principal = principal
        return principal
    limiter.check(
        "auth-failure",
        source_ip(request),
        settings.auth_fail_limit_per_minute,
        block_seconds=900,
    )
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
