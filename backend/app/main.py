"""Voda EHRs FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.schemas.response import failure
from app.storage.document_storage import ensure_bucket

configure_logging()
logger = get_logger("application")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hook.

    - Ensures the MinIO bucket exists.
    - Runs the data seeding script on first start‑up if the database appears empty.
      This makes the integration tests deterministic without requiring an external
      seeding step.
    """
    # Ensure the object‑storage bucket exists before any upload can arrive.
    try:
        ensure_bucket()
    except Exception as exc:  # noqa: BLE001 - startup should not crash on storage
        logger.warning("Could not ensure MinIO bucket on startup: %s", exc)

    # Run seeding if no users exist (idempotent). This covers test environments
    # where the database is freshly created for each run.
    from sqlalchemy.orm import Session
    from app.database.session import SessionLocal
    from app.repositories import user_repository
    from app import seed as seed_module

    db: Session = SessionLocal()
    try:
        existing_users = user_repository.list_users(db)
        # Determine if any of the expected clinician emails are missing.
        from app.seed import CLINICIAN_USERS
        expected_emails = {c["email"] for c in CLINICIAN_USERS}
        existing_emails = {u.email for u in existing_users}
        missing = expected_emails - existing_emails
        if missing:
            logger.info("Missing clinician users (%s) – running data seeding.", ", ".join(missing))
            seed_module.main()
        else:
            logger.debug("All expected clinicians present – skipping seeding.")
    finally:
        db.close()

    logger.info("Voda EHRs backend started in %s mode.", settings.environment)
    yield


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Zero-Trust Electronic Health Records platform (Phase 1 foundation).",
    lifespan=lifespan,
)


# --- HTTPS Enforcement Middleware ---
@app.middleware("http")
async def https_redirect(request: Request, call_next):
    """Redirect HTTP to HTTPS in production environments."""
    if settings.environment == "production":
        # Check for HTTPS or forwarded proto header
        is_https = request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https"
        if not is_https:
            https_url = str(request.url.replace(scheme="https"))
            return JSONResponse(
                status_code=307,
                headers={"Location": https_url},
                content={"message": "Redirecting to HTTPS"}
            )
    return await call_next(request)


# --- Middleware ---
# Rate limiting first (before auth)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# --- Standardized error envelopes ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=failure(str(exc.detail)))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content=failure("Validation failed.", errors))


# --- Routes ---
app.include_router(api_router, prefix=settings.api_v1_prefix)
