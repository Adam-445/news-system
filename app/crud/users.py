from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import models
from app.schemas import UserCreate
from uuid import UUID


class UserService:
    @staticmethod
    def get_all_users(
        db: Session,
        limit: int = 10,
        skip: int = 0,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[models.User]:
        query = db.query(models.User)
        sort_column = getattr(models.User, sort_by, None)
        if sort_column:
            query = query.order_by(
                sort_column.desc() if order == "desc" else sort_column.asc()
            )
        return query.limit(limit).offset(skip).all()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> models.User:
        try:
            user = models.User(**user_data.model_dump())
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> models.User:
        return db.query(models.User).filter(models.User.id == user_id).first()

    @staticmethod
    def search_users(
        db: Session,
        id: Optional[UUID] = None,
        email: Optional[str] = None,
        username: Optional[str] = None,
    ) -> List[models.User]:
        query = db.query(models.User)
        if id:
            query = query.filter(models.User.id == id)
        if email:
            query = query.filter(models.User.email == email)
        if username:
            query = query.filter(models.User.username.contains(username))
        return query.all()

    @staticmethod
    def delete_user(db: Session, user_id: UUID) -> bool:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
        user.is_active = False
        db.commit()
        return True

    @staticmethod
    def undelete_user(db: Session, user_id: UUID) -> bool:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
        user.is_active = True
        db.commit()
        return True

    @staticmethod
    def update_user(db: Session, user_id: UUID, new_data: UserCreate):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return None

        updated_fields = new_data.model_dump(exclude_unset=True)
        for field, value in updated_fields.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user
