# database.py
from sqlalchemy.orm import sessionmaker, Session, with_loader_criteria
from sqlalchemy import event
from app.db.connection import engine
from app.db import models

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

@event.listens_for(SessionLocal, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    session = execute_state.session
    is_admin = session.info.get("is_admin", False)
    
    if not is_admin:
        # Apply to ALL operations (SELECT/UPDATE/DELETE)
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                models.Article,
                lambda cls: cls.is_deleted == False,
                include_aliases=True
            ),
            with_loader_criteria(
                models.User,
                lambda cls: cls.is_deleted == False,
                include_aliases=True
            )
        )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
