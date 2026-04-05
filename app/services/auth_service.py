"""
Authentication service — login, token creation, and refresh logic.

Orchestrates security utilities and user repository.  The API layer
calls this service; this service never touches HTTP request objects.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories import user_repo
from app.schemas.auth import TokenResponse


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> TokenResponse:
    """Validate credentials and return an access + refresh token pair."""
    user = await user_repo.get_by_email(db, email)

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated. Contact an administrator.",
        )

    return _build_tokens(str(user.id), user.role.value)


async def refresh_access_token(
    db: AsyncSession, refresh_token: str
) -> TokenResponse:
    """Issue a new token pair from a valid refresh token."""
    payload = decode_token(refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await user_repo.get_by_id(db, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists or is deactivated",
        )

    return _build_tokens(str(user.id), user.role.value)


# ── Private ───────────────────────────────────────────────────────────────────


def _build_tokens(user_id: str, role: str) -> TokenResponse:
    """DRY helper — builds the token pair for a given user."""
    data = {"sub": user_id, "role": role}
    return TokenResponse(
        access_token=create_access_token(data),
        refresh_token=create_refresh_token(data),
    )
