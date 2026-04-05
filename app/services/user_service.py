"""
User management service — create, update, list, deactivate.

Business rules:
  - Duplicate email check on creation
  - Password is hashed before storage
  - Admin-only guard is enforced at the API layer, not here
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserResponse, UserUpdate


async def create_user(db: AsyncSession, data: UserCreate) -> UserResponse:
    """Register a new user after checking for duplicate email."""
    existing = await user_repo.get_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email {data.email} is already registered",
        )

    user = await user_repo.create_user(
        db,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    return UserResponse.model_validate(user)


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> UserResponse:
    """Fetch a single user by ID."""
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)


async def list_users(
    db: AsyncSession, page: int = 1, limit: int = 20
) -> tuple[list[UserResponse], int]:
    """Return a paginated list of users."""
    skip = (page - 1) * limit
    users, total = await user_repo.list_users(db, skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users], total


async def update_user(
    db: AsyncSession, user_id: uuid.UUID, data: UserUpdate
) -> UserResponse:
    """Partially update a user's mutable fields."""
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    user = await user_repo.update_user(db, user, **update_data)
    return UserResponse.model_validate(user)


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> UserResponse:
    """Soft-deactivate a user (set is_active = False)."""
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user = await user_repo.update_user(db, user, is_active=False)
    return UserResponse.model_validate(user)
