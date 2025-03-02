from sqlalchemy import select, exc
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from time import sleep

from app.core import security
from app.core.config import settings
from app.core.logging import logger
from app.db.connection import engine
from app.db.models.permission import Permission
from app.db.models.role import Role
from app.db.models.user import User

def seed_roles_permissions(session: Session, seed_default_users: bool = False) -> bool:
    """ 
    Seeds roles, permissions, and optionally default users into the database.

    - Roles and permissions are inserted if they do not already exist (idempotency).
    - Permissions are assigned to roles in an additive manner (new permissions do not override existing ones).
    - Default users are created if `seed_default_users` is True.

    Args:
        session (Session): SQLAlchemy session object.
        seed_default_users (bool): Whether to seed default users (typically for development).

    Returns:
        bool: True if seeding succeeds, False if it fails due to expected errors.
    """
    try:
        with session.begin():
            # Insert roles if they do not already exist to ensure idempotency
            session.execute(
                insert(Role).values([
                    {"name": "admin", "description": "Full access"},
                    {"name": "moderator", "description": "Limited access"},
                    {"name": "regular", "description": "Basic access"},
                ]).on_conflict_do_nothing()
            )

            # Insert permissions if they do not already exist to avoid duplicate entries
            session.execute(
                insert(Permission).values([
                    {"name": "create_article", "description": "Create articles"},
                    {"name": "delete_article", "description": "Delete articles"},
                    {"name": "update_article", "description": "Update articles"},
                    {"name": "delete_user", "description": "Delete users"},
                ]).on_conflict_do_nothing()
            )

            # Assign permissions to admin and moderator roles in an additive manner
            # This prevents overwriting existing permissions while ensuring new ones are included
            admin = session.scalars(select(Role).filter_by(name="admin")).first()
            moderator = session.scalars(select(Role).filter_by(name="moderator")).first()
            all_perms = session.scalars(select(Permission)).all()
            mod_perms = [p for p in all_perms if p.name != "delete_user"]

            if admin:
                existing = {p.name for p in admin.permissions}
                admin.permissions.extend([p for p in all_perms if p.name not in existing])
                
            if moderator:
                existing = {p.name for p in moderator.permissions}
                moderator.permissions.extend([p for p in mod_perms if p.name not in existing])

            # Bulk user creation
            if seed_default_users:
                session.execute(
                    insert(User).values([
                        {
                            "username": f"{role}_user",
                            "email": f"{role}@example.com",
                            "password": security.get_password_hash("TestPass123!"),
                            "role_name": role
                        } for role in ["regular", "moderator", "admin"]
                    ]).on_conflict_do_nothing()
                )

        return True

    except exc.IntegrityError as e:
        logger.error(f"Data conflict: {e}")
        return False
    except exc.OperationalError as e:
        logger.error(f"Database connection issue: {e}")
        raise  # Retryable
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False

def main():
    """
    Entry point for database seeding.

    - Runs only in development, CI, or staging environments to prevent accidental production modification.
    - Implements retry logic (exponential backoff) to handle temporary database connection issues.

    Raises:
        exc.OperationalError: If database remains unreachable after retries.
    """
    # Prevent accidental modifications in production
    if settings.environment not in {"development", "ci", "staging"}:
        logger.warning("Production seeding disabled")
        return

    # Number of retry attempts for transient failures
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with Session(engine) as session:
                if seed_roles_permissions(session, settings.environment == "development"):
                    logger.info("Seeding successful")
                    return
        except exc.OperationalError:
            if attempt == max_retries -1:
                logger.critical("Seeding failed after retries")
                raise
            sleep(2 ** attempt)
            logger.warning(f"Retrying seeding (attempt {attempt+1})")

if __name__ == "__main__":
    main()