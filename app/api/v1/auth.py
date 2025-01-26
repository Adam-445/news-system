from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import models
import app.schemas as schemas
import app.core.security as security
from app.db.database import get_db
from app.crud.users import UserService

router = APIRouter()


@router.post(
    "/signup", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse
)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    new_user = UserService.create_user(db, user)
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this email or username already exists.",
        )
    return new_user


@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db),) -> schemas.Token:
    user = (
        db.query(models.User)
        .filter(models.User.username == user_credentials.username)
        .first()
    )

    if not (
        user and security.verify_password(
            user_credentials.password, user.password)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentails."
        )

    # create a token
    access_token = security.create_access_token(data={"user_username": user.username})

    # return token
    return schemas.Token(access_token=access_token, token_type="bearer")
