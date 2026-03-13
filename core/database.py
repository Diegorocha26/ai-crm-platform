from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from core.config import get_settings

settings = get_settings()

# Create async engine with pool_pre_ping for stability
engine = create_async_engine(
    settings.DATABASE_ASYNC_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to provide an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
