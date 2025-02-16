from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import event
from app.db.connection import engine
from app.db.query import SoftDeleteQuery
from app.db.events import handle_include_deleted

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    query_cls=SoftDeleteQuery,
)

# Register event listener
event.listen(Session, "do_orm_execute", handle_include_deleted)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
