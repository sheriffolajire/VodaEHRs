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
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.schemas.response import failure

configure_logging()
logger = get_logger("application")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Voda EHRs backend started in %s mode.", settings.environment)
    yield


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="Electronic Health Records platform.",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Standardized error envelopes
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


# Routes
app.include_router(api_router, prefix=settings.api_v1_prefix)
