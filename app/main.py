"""
FastAPI application factory.

Wires together:
  - Lifespan (DB table creation + admin seed on startup)
  - CORS middleware
  - Global error handlers
  - V1 API router
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.middleware.error_handler import register_error_handlers
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zorvyn")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed admin.  Shutdown: dispose engine."""
    # Create tables (in production, Alembic handles migrations instead)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default admin if not exists
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        if result.scalar_one_or_none() is None:
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name="System Admin",
                role=UserRole.ADMIN,
            )
            db.add(admin)
            await db.commit()
            logger.info("✓ Default admin seeded: %s", settings.ADMIN_EMAIL)

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Zorvyn Finance API",
        description="A role-based financial records management backend",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow all origins for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    register_error_handlers(app)

    # Routes
    app.include_router(v1_router)

    return app


app = create_app()
