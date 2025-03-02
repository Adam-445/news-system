import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.rate_limiting import rate_limiter
from app.db.base import Base
from app.db.connection import engine
from app.db.database import _add_soft_delete_filter, get_db
from app.db.seed import seed_roles_permissions
from app.main import app

# Set the environment to "test"
settings.environment = "test"

# Define the test database URL
SQLALCHEMY_DATABASE_URL = f"{settings.database_url}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Provide an event loop policy instead of overriding event_loop directly."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def redis_client():
    """Session-scoped Redis client with proper cleanup."""
    redis = Redis.from_url(
        f"{settings.redis_url}/1",
        decode_responses=True,
        socket_connect_timeout=2,
        retry_on_timeout=True,
        protocol=3,
    )
    yield redis
    await redis.aclose()


@pytest.fixture(scope="function", autouse=True)
async def clean_redis(redis_client: Redis) -> None:
    """Flush Redis completely before each test runs."""
    await redis_client.flushdb()
    await redis_client.script_flush()


# --- Override the rate limiter dependency to disable rate limiting ---
@pytest.fixture(scope="function", autouse=True)
def _disable_rate_limits():
    """
    Override the rate_limiter dependency so that endpoints do not enforce rate limiting
    during tests.
    """
    # Provide a dummy dependency accepting the same arguments but doing nothing.
    app.dependency_overrides[rate_limiter] = lambda times, seconds: None
    yield
    app.dependency_overrides.pop(rate_limiter, None)


# ---------------------------------------------------------------------


@pytest.fixture(scope="function")
def db() -> Generator[sessionmaker, None, None]:
    """Transactional database fixture with rollback."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create test session with event listeners
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=Session,
    )
    event.listens_for(TestingSessionLocal, "do_orm_execute")(_add_soft_delete_filter)

    db = TestingSessionLocal()
    seed_roles_permissions(session=db, seed_default_users=True)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db: sessionmaker, clean_redis: None):
    """
    Test client fixture that forces rate limiter initialization during startup.

    Even though the environment is "test", setting the flag ensures that the startup
    event calls init_limiter on the same event loop as TestClient. Meanwhile, the
    dependency override (_disable_rate_limits) ensures rate limiting isn’t enforced.
    """
    # Force rate limiter initialization in the app’s lifespan.
    app.state.force_rate_limiter_init = True

    def override_get_db() -> Generator[sessionmaker, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --- Authentication header fixtures remain unchanged ---
@pytest.fixture(scope="function")
def auth_headers(client: TestClient) -> callable:
    """Auth header factory with rate limit protection."""

    def _get_headers(role: str) -> dict:
        # Test-specific authentication bypass
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"{role}_user",
                "password": "TestPass123!",
            },
        )
        response.raise_for_status()
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _get_headers


@pytest.fixture(scope="function")
def regular_headers(auth_headers: callable) -> dict:
    return auth_headers("regular")


@pytest.fixture(scope="function")
def moderator_headers(auth_headers: callable) -> dict:
    return auth_headers("moderator")


@pytest.fixture(scope="function")
def admin_headers(auth_headers: callable) -> dict:
    return auth_headers("admin")

@pytest.fixture
def test_user(client):
    user_data = {
        "email": "test_user@example.com",
        "username": "test_user",
        "password": "TestPass123!",
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    return response.json()
