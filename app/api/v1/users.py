"""
User management routes — Admin only.

CRUD operations on users with pagination.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.database import get_db
from app.models.user import UserRole
from app.schemas.record import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

# All routes require ADMIN role
AdminDep = Depends(require_role(UserRole.ADMIN))


@router.post("/", response_model=UserResponse, status_code=201, dependencies=[AdminDep])
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user (admin only)."""
    return await user_service.create_user(db, body)


@router.get("/", response_model=PaginatedResponse[UserResponse], dependencies=[AdminDep])
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination (admin only)."""
    users, total = await user_service.list_users(db, page=page, limit=limit)
    import math
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if limit else 0,
    )


@router.get("/{user_id}", response_model=UserResponse, dependencies=[AdminDep])
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single user by ID (admin only)."""
    return await user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse, dependencies=[AdminDep])
async def update_user(
    user_id: uuid.UUID, body: UserUpdate, db: AsyncSession = Depends(get_db)
):
    """Update user fields (admin only)."""
    return await user_service.update_user(db, user_id, body)


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    dependencies=[AdminDep],
)
async def deactivate_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Soft-deactivate a user (admin only)."""
    return await user_service.deactivate_user(db, user_id)
