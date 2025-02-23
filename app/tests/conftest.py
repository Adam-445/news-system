# conftest.py
import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio
from typing import Generator

from app.main import app
from app.db.base import Base
from app.db.database import get_db
from app.core.config import settings
from app.db.seed import seed_roles_permissions
from app.core.rate_limiting import init_limiter

# Define the test database URL
SQLALCHEMY_DATABASE_URL = f"{settings.database_url}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a session-scoped event loop"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def redis_client():
    """Session-scoped Redis client with proper cleanup"""
    redis = Redis.from_url(
        f"{settings.redis_url}/1",
        decode_responses=True,
        socket_connect_timeout=2,
        retry_on_timeout=True,
        protocol=3
    )
    yield redis
    await redis.aclose()

@pytest.fixture(scope="function")
async def clean_redis(redis_client: Redis) -> None:
    """Flush Redis before each test for complete isolation"""
    await redis_client.script_flush()
    await redis_client.flushdb()

@pytest.fixture(scope="function")
def db() -> Generator[sessionmaker, None, None]:
    """Transactional database fixture with rollback"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_roles_permissions(session=db, seed_default_users=True)
    
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(scope="function")
async def client(db: sessionmaker, redis_client: Redis, clean_redis: None):
    """Test client with rate limiter initialization"""
    await init_limiter(redis_client=redis_client, is_test=True, enabled=True)
    
    def override_get_db() -> Generator[sessionmaker, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# TODO: Fix rate limiting in tests
@pytest.fixture(scope="function")
def auth_headers(client: TestClient) -> callable:
    """Auth header factory with rate limit protection"""
    def _get_headers(role: str) -> dict:
        # Test-specific authentication bypass
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": f"{role}_user",
                "password": "TestPass123!",
                # "test_mode": "true"
            }
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