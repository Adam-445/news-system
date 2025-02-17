from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone

from app.core.errors import ConflictError, NotFoundError, BadRequestError
from app.db import models
from app.schemas import UserCreate, UserUpdate
from app.core import security


class UserService:
    @staticmethod
    def get_all_users(
        db: Session,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[models.User]:
        allowed_sort_fields = {"created_at", "username", "email"}

        query = db.query(models.User)
        if sort_by not in allowed_sort_fields:
            BadRequestError(
                message="Invalid field", detail=f"Invalid sort field: {sort_by}"
            )
        sort_column = getattr(models.User, sort_by, None)
        if sort_column:
            query = query.order_by(
                sort_column.desc() if order == "desc" else sort_column.asc()
            )
        return query.limit(limit).offset(skip).all()

    @staticmethod
    def search_users(
        db: Session,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> List[models.User]:
        query = db.query(models.User)
        if email:
            query = query.filter(models.User.email.ilike(email))
        if username:
            query = query.filter(models.User.username.ilike(f"%{username}%"))

        users = query.all()
        if not users:
            raise NotFoundError(resource="User")

        return users

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> models.User:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise NotFoundError(resource="User", identifier=user_id)
        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> models.User:
        try:
            user_data.password = security.get_password_hash(user_data.password)
            user = models.User(**user_data.model_dump(), role_name="regular")
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise ConflictError(
                resource="User",
            )

    @staticmethod
    def delete_user(db: Session, user_id: UUID) -> models.User:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise NotFoundError(resource="User", identifier=user_id)
        if user.is_deleted:
            raise ConflictError(resource="User")

        user.is_deleted = True
        user.deleted_at = datetime.now(tz=timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def undelete_user(db: Session, user_id: UUID) -> models.User:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise NotFoundError(resource="User", identifier=user_id)
        if not user.is_deleted:
            raise ConflictError(resource="User")

        user.is_deleted = False
        user.deleted_at = None
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user_id: UUID, new_data: UserUpdate) -> models.User:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise NotFoundError(resource="User", identifier=user_id)

        updated_fields = new_data.model_dump(exclude_unset=True)

        # Ensure new email or username is not already taken
        if "email" in updated_fields or "username" in updated_fields:
            existing_user = (
                db.query(models.User)
                .filter(
                    (models.User.email == updated_fields.get("email", user.email))
                    | (
                        models.User.username
                        == updated_fields.get("username", user.username)
                    )
                )
                .filter(models.User.id != user_id)
                .first()
            )
            if existing_user:
                raise ConflictError(
                    resource="User", message="Email or username is already in use."
                )

        if "password" in updated_fields:
            updated_fields["password"] = security.get_password_hash(
                updated_fields["password"]
            )

        for field, value in updated_fields.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user
