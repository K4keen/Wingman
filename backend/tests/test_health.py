from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError

from app.db import get_session
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # ASGITransport calls the app in-process: no server, no port.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def clear_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_health_ok_when_db_answers(client: AsyncClient) -> None:
    # Uses the real database from DATABASE_URL (docker compose locally, a service container in CI).
    resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": "ok"}


class FailingSession:
    """Stands in for AsyncSession; every query raises the given error."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise self.error


@pytest.mark.parametrize(
    "error",
    [
        # Postgres is down: the driver cannot even open a TCP connection.
        ConnectionRefusedError("connection refused"),
        # Postgres is up but refuses us (starting up, bad password...): SQLAlchemy wraps it.
        OperationalError("SELECT 1", {}, Exception("the database system is starting up")),
    ],
    ids=["connection-refused", "operational-error"],
)
@pytest.mark.usefixtures("clear_overrides")
async def test_health_503_when_db_fails(client: AsyncClient, error: Exception) -> None:
    async def failing_session() -> AsyncIterator[FailingSession]:
        yield FailingSession(error)

    app.dependency_overrides[get_session] = failing_session

    resp = await client.get("/health")

    assert resp.status_code == 503
    assert resp.json() == {"detail": "Database unavailable"}
