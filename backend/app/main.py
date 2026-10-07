"""FastAPI entry point. Run with: uv run uvicorn app.main:app --reload"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import engine, get_session

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    # Close pooled connections cleanly on shutdown.
    await engine.dispose()


app = FastAPI(title="Wingman", lifespan=lifespan)


@app.get("/health")
async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, str]:
    """Liveness + DB check: 200 when the database answers, 503 otherwise."""
    try:
        await session.execute(text("SELECT 1"))
    # SQLAlchemyError: the DB answered with an error (starting up, auth failed, ...).
    # OSError: no connection at all (refused, unreachable) - raised by the driver, not wrapped.
    # Anything else is a bug in our code and should surface as a 500, not be hidden as a 503.
    except (SQLAlchemyError, OSError) as exc:
        logger.warning("Health check failed: database unavailable: %r", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable"
        ) from exc
    return {"status": "ok", "db": "ok"}
