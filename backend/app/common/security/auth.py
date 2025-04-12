import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from backend.app.common.config.settings import settings
from backend.app.modules.auth.schemas.token import TokenData
from backend.app.shared.infrastructure.redis.client import RedisManager

# JWT configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.jwt_refresh_token_expire_days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash password
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# verify hashed passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Create JWT access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    data: dict,
    expires_delta: timedelta = timedelta(days=settings.jwt_refresh_token_expire_days),
) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    to_encode["type"] = "refresh"
    # JWTs are long strings, which increase Redis memory usage
    to_encode["jti"] = str(uuid.uuid4())
    print("JTI", to_encode["jti"])
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        role: str = payload.get("role")

        if not username:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except jwt.InvalidTokenError:
        raise credentials_exception
    return token_data


async def verify_refresh_token(token: str, credentials_exception):
    if await RedisManager.is_token_blacklisted(token):
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        username: str = payload.get("username")
        role: str = payload.get("role")
        jti: str = payload.get("jti")

        if not username:
            raise credentials_exception

        token_data = TokenData(jti=jti, username=username, role=role)
    except jwt.InvalidTokenError:
        raise credentials_exception
    return token_data
