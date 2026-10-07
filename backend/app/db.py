"""Database engine (connection pool, one per process) and per-request sessions."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# pool_pre_ping checks a connection before handing it out, so dropped connections are replaced.
engine = create_async_engine(settings.database_url, pool_size=5, pool_pre_ping=True)

# expire_on_commit=False keeps attributes loaded after commit; lazy reloads would fail under async.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, closed when the request finishes."""
    async with SessionLocal() as session:
        yield session
