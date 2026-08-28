from __future__ import annotations

import re
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.api.routes import router
from app.auth.service import (
    DASHBOARD_SESSION_COOKIE,
    create_dashboard_session,
    source_ip,
    verify_dashboard_password,
)
from app.config import Settings, get_settings
from app.db.models import AuditEvent
from app.db.session import SessionLocal
from app.rate_limit.service import RateLimiter, get_rate_limiter


settings = get_settings()
app = FastAPI(
    title="CCN Brief Task API",
    version="1.0.0",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
)
app.include_router(router)
WEB_ROOT = Path(__file__).resolve().parent / "web"
TASK_PATH = re.compile(r"^/api/v1/tasks/([^/]+)")


class DashboardLogin(BaseModel):
    password: str = Field(min_length=1, max_length=1024)


@app.get("/dashboard-assets/{asset_name}", include_in_schema=False)
def dashboard_asset(asset_name: str) -> FileResponse:
    if asset_name not in {"dashboard.css", "dashboard.js"}:
        raise HTTPException(status_code=404, detail={"code": "asset_not_found", "message": "Asset not found"})
    return FileResponse(
        WEB_ROOT / asset_name,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@app.get("/dashboard", include_in_schema=False)
@app.get("/dashboard/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(
        WEB_ROOT / "dashboard.html",
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self' https://media.githubusercontent.com; "
                "base-uri 'none'; "
                "frame-ancestors 'none'; form-action 'self'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )


@app.post("/dashboard-auth/login", include_in_schema=False)
def dashboard_login(
    body: DashboardLogin,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> dict[str, str]:
    if not settings.dashboard_password_hash:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "dashboard_unavailable", "message": "Dashboard password is not configured"},
        )
    if not verify_dashboard_password(body.password, settings.dashboard_password_hash):
        limiter.check(
            "auth-failure",
            source_ip(request),
            settings.auth_fail_limit_per_minute,
            block_seconds=900,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Invalid credentials"},
        )
    response.set_cookie(
        DASHBOARD_SESSION_COOKIE,
        create_dashboard_session(settings),
        max_age=settings.dashboard_session_ttl_seconds,
        httponly=True,
        secure=settings.dashboard_cookie_secure,
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"status": "success"}


@app.post("/dashboard-auth/logout", include_in_schema=False)
def dashboard_logout(response: Response, settings: Settings = Depends(get_settings)) -> dict[str, str]:
    response.delete_cookie(
        DASHBOARD_SESSION_COOKIE,
        httponly=True,
        secure=settings.dashboard_cookie_secure,
        samesite="strict",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"status": "success"}


@app.middleware("http")
async def audit_request(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/healthz":
        principal = getattr(request.state, "principal", None)
        match = TASK_PATH.match(request.url.path)
        event = AuditEvent(
            method=request.method,
            path=request.url.path[:256],
            source_ip=source_ip(request),
            key_fingerprint=principal.fingerprint if principal else None,
            task_id=match.group(1)[:128] if match else None,
            status_code=response.status_code,
        )
        try:
            with SessionLocal() as session:
                session.add(event)
                session.commit()
        except Exception:  # The audit sink must never expose or replace the API response.
            pass
    return response


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_error(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "http_error", "message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "error": detail},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"location": list(item["loc"]), "message": item["msg"], "type": item["type"]}
        for item in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "error": {"code": "validation_error", "message": "Invalid request", "details": errors},
        },
    )
