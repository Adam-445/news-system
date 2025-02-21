from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from app.db import models
import app.schemas as schemas
import app.core.security as security
from app.db.database import get_db
from app.crud.users import UserService
from app.core.errors import ConflictError, UnauthorizedError
from app.core.rate_limiting import strict_rate_limiter

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
    # TODO: Implement RateLimiter to prevent brute-force attacks
    dependencies=[Depends(strict_rate_limiter)]
)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> schemas.Token:
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

    # Return token
    return schemas.Token(access_token=access_token, token_type="bearer")
