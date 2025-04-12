from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.common.exceptions.http import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from backend.app.common.security import auth
from backend.app.modules.users.models.user import User
from backend.app.modules.users.schemas.user import UserCreate, UserUpdate


class UserService:
    @staticmethod
    def get_all_users(
        db: Session,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[User]:

        allowed_sort_fields = {"created_at", "username", "email"}

        if sort_by not in allowed_sort_fields:
            raise BadRequestError(
                message="Invalid field", detail=f"Invalid sort field: {sort_by}"
            )

        stmt = select(User)

        sort_column = getattr(User, sort_by)
        if sort_column:
            stmt = stmt.order_by(
                sort_column.desc() if order == "desc" else sort_column.asc()
            )

        stmt = stmt.offset(skip).limit(limit)

        return db.execute(stmt).scalars().all()

    @staticmethod
    def search_users(
        db: Session,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> List[User]:
        stmt = select(User)

        if email:
            stmt = stmt.where(User.email.ilike(email))
        if username:
            stmt = stmt.where(User.username.ilike(f"%{username}%"))

        users = db.execute(stmt).scalars().all()

        if not users:
            raise NotFoundError(resource="User")

        return users

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User:
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            raise NotFoundError(resource="User", identifier=user_id)

        return user

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        try:
            user_data.password = auth.get_password_hash(user_data.password)
            stmt = (
                insert(User)
                .values(**user_data.model_dump(), role_name="regular")
                .returning(User)
            )
            user = db.execute(stmt).scalar_one_or_none()
            db.commit()
            return user
        except IntegrityError:
            db.rollback()
            raise ConflictError(
                resource="Email or username",
            )

    @staticmethod
    def delete_user(db: Session, user_id: UUID) -> dict:
        stmt = select(User).where(User.id == user_id).with_for_update()
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            raise NotFoundError(resource="User", identifier=user_id)

        if user.is_deleted:
            raise ConflictError("User is already deleted")

        current_time = datetime.now(timezone.utc)
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_deleted=True, deleted_at=current_time)
        )

        db.execute(stmt)
        db.commit()

    @staticmethod
    def undelete_user(db: Session, user_id: UUID) -> dict:
        stmt = select(User).where(User.id == user_id).with_for_update()
        user = db.execute(stmt).scalar_one_or_none()

        if not user:
            raise NotFoundError(resource="User", identifier=user_id)

        if not user.is_deleted:
            raise ConflictError("User is already active")

        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_deleted=False, deleted_at=None)
        )

        db.execute(stmt)
        db.commit()

    @staticmethod
    def update_user(db: Session, user_id: UUID, new_data: UserUpdate) -> User:
        # Atomic single-query update
        update_dict = new_data.model_dump(exclude_unset=True)

        if "password" in update_dict:
            update_dict["password"] = auth.get_password_hash(update_dict["password"])

        # Case-insensitive check and update in single operation
        stmt = (
            update(User).where(User.id == user_id).values(update_dict).returning(User)
        )

        updated_user = db.execute(stmt).scalar_one_or_none()
        db.commit()

        if not updated_user:
            raise NotFoundError(resource="User", identifier=user_id)

        return updated_user
