import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import UUID

from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings
from app.db.seed import seed_roles_permissions

# Define the test database URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.database_username}:{settings.database_password}"
    f"@{settings.database_hostname}/{settings.database_name}_test"
)  # Note the "_test" suffix to isolate the test database

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Create tables in the test database
    Base.metadata.create_all(bind=engine)

    # Create a new session for tests
    db = TestingSessionLocal()

    # Seed the database with default roles and permissions
    seed_roles_permissions(session=db, seed_default_users=True)

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Override the dependency to use the test DB session
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# Fixture to obtain authentication headers
@pytest.fixture
def regular_headers(client):
    login_data = {"username": "regular_user", "password": "TestPass123!"}
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def moderator_headers(client):
    login_data = {"username": "moderator_user", "password": "TestPass123!"}
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    login_data = {"username": "admin_user", "password": "TestPass123!"}
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user(client):
    user_data = {
        "email": "test_user@example.com",
        "username": "test_user",
        "password": "TestPass123!",
    }
    response = client.post("/api/v1/auth/signup", json=user_data)
    return response.json()
