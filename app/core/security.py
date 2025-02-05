from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext

from app.core.config import settings
import app.schemas as schemas
import jwt


# JWT configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")

        if not username:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
        print(token_data)
    except jwt.InvalidTokenError:
        raise credentials_exception
    return token_data
