"""Authentication and session endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
)
from app.schemas.response import success
from app.schemas.user import UserOut
from app.services import auth_service
from app.core.config import settings
from app.services.exceptions import AuthError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    try:
        access_token, refresh_token, user = auth_service.login(
            db, payload.email, payload.password, _client_ip(request)
        )
    except AuthError as exc:
        db.commit()  # persist the audited login failure
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    db.commit()
    # Set refresh token as HttpOnly, Secure, SameSite=Strict cookie.
    # The cookie will be sent automatically on subsequent requests.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/v1/auth/refresh",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )
    return success(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        },
        message="Login successful.",
    )


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    """Refresh the access token using the HttpOnly refresh‑token cookie.

    The client no longer sends the refresh token in the request body; instead
    the backend reads the ``refresh_token`` cookie (set on login/previous
    refresh). This mitigates XSS leakage of the refresh token.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token missing.")
    try:
        access_token, new_refresh, _ = auth_service.refresh(
            db, refresh_token, _client_ip(request)
        )
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    db.commit()
    # Update the HttpOnly refresh token cookie with the new token.
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/v1/auth/refresh",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )
    return success(
        data={"access_token": access_token, "token_type": "bearer"},
        message="Token refreshed.",
    )


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    # Prefer the HttpOnly cookie if the payload does not contain a token.
    token = payload.refresh_token or request.cookies.get("refresh_token")
    if token:
        auth_service.logout(db, token, _client_ip(request))
    # Clear the cookie on logout.
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
    db.commit()
    return success(message="Logged out.")


@router.post("/password-reset/request")
def password_reset_request(
    payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)
) -> dict:
    # The response is identical whether or not the email exists (no enumeration).
    auth_service.request_password_reset(db, payload.email, _client_ip(request))
    db.commit()
    return success(message="If the account exists, a reset link has been sent.")


@router.post("/password-reset/confirm")
def password_reset_confirm(
    payload: PasswordResetConfirm, request: Request, db: Session = Depends(get_db)
) -> dict:
    try:
        auth_service.confirm_password_reset(
            db, payload.token, payload.new_password, _client_ip(request)
        )
    except ValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.commit()
    return success(message="Password updated.")
