from fastapi import APIRouter, Body, Cookie, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import app.core.security as security
import app.schemas as schemas
from app.core.config import settings
from app.core.errors import UnauthorizedError
from app.core.rate_limiting import rate_limiter
from app.core.redis import RedisManager
from app.crud.users import UserService
from app.db import models
from app.db.database import get_db

router = APIRouter()


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserResponse,
    summary="Register a new user",
    description="""
    This endpoint registers a new user with email verification and password validation.

    ### Password Requirements:
    - Must be at least **10 characters** long
    - Must contain **at least one uppercase letter**
    - Must contain **at least one number**

    ### Email Requirements:
    - The email address must be **valid**
    - The email **cannot be already in use**

    ### Response:
    - Returns the newly created user object (without the password).
    - If the email or username already exists, a **409 Conflict** error is raised.
    """,
    responses={
        201: {
            "description": "User successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "username": "johndoe",
                        "email": "johndoe@example.com",
                        "role_name": "regular",
                        "created_at": "2024-02-20T14:30:00Z",
                        "is_deleted": False,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "examples": {
                        "short_password": {
                            "summary": "Password too short",
                            "value": {
                                "error": "Bad Request",
                                "detail": "Password must be at least 10 characters",
                            },
                        },
                        "missing_number": {
                            "summary": "Password missing number",
                            "value": {
                                "error": "Bad Request",
                                "detail": "Password must contain a number",
                            },
                        },
                    }
                }
            },
        },
        409: {
            "description": "Conflict - Username or email already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Conflict",
                        "detail": "Username or email already exists",
                    }
                }
            },
        },
    },
)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Creates a new user with hashed password and assigns the default role.
    """
    return UserService.create_user(db, user)


@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Authenticate User & Generate Token",
    description="""
    This endpoint allows registered users to log in and receive an authentication token.

    ### Request:
    - `username`: The user's registered username.
    - `password`: The correct password for authentication.

    ### Response:
    - If login is **successful**, returns an `access_token` which should be included in the `Authorization` header (`Bearer <token>`).
    - If login **fails**, a `401 Unauthorized` error is returned.

    ### Example Usage:
    ```http
    POST /api/v1/auth/login
    Content-Type: application/x-www-form-urlencoded

    username=johndoe&password=SuperSecret123
    ```

    ### Possible Errors:
    - `401 Unauthorized`: Invalid username or password.
    """,
    responses={
        200: {
            "description": "Successful Authentication",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        401: {
            "description": "Invalid Credentials",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Unauthorized",
                        "detail": "Invalid username or password",
                    }
                }
            },
        },
    },
    dependencies=[Depends(rate_limiter(5, 60))],
)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Authenticate user and return an access token.
    """
    # Find user by username
    user = (
        db.query(models.User)
        .filter(models.User.username == user_credentials.username)
        .first()
    )

    # Validate credentials
    if not (
        user and security.verify_password(user_credentials.password, user.password)
    ):
        raise UnauthorizedError(detail="Invalid username or password")

    # Generate access token
    access_token = security.create_access_token(
        data={"username": user.username, "role": user.role.name}
    )

    # Generate refresh token
    refresh_token = security.create_refresh_token(
        data={"username": user.username, "role": user.role.name}
    )

    # Store refresh token in HTTP-only Secure Cookie
    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Strict",
    )

    return response


@router.post("/logout")
async def logout(refresh_token: str = Cookie(None)):
    if refresh_token:
        # Decode to get JTI
        token_data = await security.verify_refresh_token(refresh_token, UnauthorizedError(detail="Could not validate refresh token"))
        jti = token_data.jti
        await RedisManager.add_to_blacklist(jti, refresh_token)

    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(key="refresh_token")
    return response


@router.post("/refresh", response_model=schemas.Token)
async def refresh_token(
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise UnauthorizedError(detail="Missing refresh token")

    # Validate refresh token
    token_data = await security.verify_refresh_token(refresh_token, UnauthorizedError(detail="Could not validate refresh token"))
    jti = token_data.jti

    # Check if the refresh token is blacklisted
    if await RedisManager.is_token_blacklisted(jti):
        raise UnauthorizedError(detail="Token revoked")

    # Generate new access token
    new_access_token = security.create_access_token(
        data={"username": token_data.username, "role": token_data.role}
    )

    # Issue a new refresh token and revoke old one
    await RedisManager.add_to_blacklist(jti, refresh_token)

    new_refresh_token = security.create_refresh_token(
        data={"username": token_data.username, "role": token_data.role}
    )


    # Set new refresh token in HTTP-only cookie
    response = JSONResponse(
        content={"access_token": new_access_token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
    )

    return response
