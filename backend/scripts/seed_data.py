from sqlalchemy import select, exc
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from time import sleep

from backend.app.common.security import auth
from backend.app.common.config.settings import settings
from backend.app.modules.admin.models.permission import Permission
from backend.app.modules.admin.models.role import Role
from backend.app.common.logging.config import logger
from backend.app.modules.users.models.user import User
from backend.app.modules.users.models.preference import UserPreference
from backend.app.shared.db.connection import engine

def seed_essential_data(session: Session) -> bool:
    """Seed core roles and permissions that are required for system operation."""
    try:
        with session.begin():
            # Upsert core roles
            session.execute(
                insert(Role).values([
                    {"name": "admin", "description": "Full access"},
                    {"name": "moderator", "description": "Limited access"},
                    {"name": "regular", "description": "Basic access"},
                ]).on_conflict_do_nothing(index_elements=["name"])
            )

            # Upsert core permissions
            session.execute(
                insert(Permission).values([
                    {"name": "create_article", "description": "Create articles"},
                    {"name": "delete_article", "description": "Delete articles"},
                    {"name": "update_article", "description": "Update articles"},
                    {"name": "delete_user", "description": "Delete users"},
                ]).on_conflict_do_nothing(index_elements=["name"])
            )

            # Assign permissions using merge strategy
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

        return True
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error seeding essential data: {e}")
        return False

def seed_admin_user(session: Session) -> bool:
    """Create initial admin user with credentials from environment variables."""
    try:
        with session.begin():
            admin_user = {
                "username": settings.initial_admin_username,
                "email": settings.initial_admin_email,
                "password": auth.get_password_hash(settings.initial_admin_password),
                "role_name": "admin"
            }
            
            session.execute(
                insert(User)
                .values(admin_user)
                .on_conflict_do_update(
                    index_elements=["email"],
                    set_={"password": admin_user["password"], "role_name": "admin"}
                )
            )
        logger.info("Admin user upserted successfully")
        return True
    except exc.SQLAlchemyError as e:
        logger.error(f"Error seeding admin user: {e}")
        return False

def seed_test_users(session: Session) -> None:
    """Seed test users only in non-production environments."""
    if settings.environment == "production":
        return

    try:
        with session.begin():
            session.execute(
                insert(User).values([
                    {
                        "username": f"{role}_user",
                        "email": f"{role}@example.com",
                        "password": auth.get_password_hash("TestPass123!"),
                        "role_name": role
                    } for role in ["regular", "moderator", "admin"]
                ]).on_conflict_do_nothing()
            )
        logger.info("Test users seeded")
    except exc.SQLAlchemyError as e:
        logger.warning(f"Test user seeding skipped: {e}")

def main():
    """
    Entry point for database seeding with production safety measures.
    Implements exponential backoff for database connectivity issues.
    """
    # Safety check for production
    if settings.environment == "production" and not settings.ALLOW_DB_SEED_IN_PROD:
        logger.warning("Production seeding requires explicit ALLOW_DB_SEED_IN_PROD=true")
        return

    max_retries = 5
    for attempt in range(max_retries):
        try:
            with Session(engine) as session:
                if not seed_essential_data(session):
                    logger.error("Essential data seeding failed")
                    return

                # Always attempt to create/update admin user in all environments
                if not seed_admin_user(session):
                    logger.error("Admin user setup failed")
                    return

                # Seed test users only in non-production
                seed_test_users(session)

                logger.info("Database seeding completed successfully")
                return
                
        except exc.OperationalError as e:
            if attempt == max_retries - 1:
                logger.critical("Seeding failed after %d attempts", max_retries)
                raise
            retry_delay = 2 ** attempt
            logger.warning("Database connection issue (attempt %d/%d), retrying in %ds...",
                         attempt+1, max_retries, retry_delay)
            sleep(retry_delay)
        except exc.SQLAlchemyError as e:
            logger.error("Fatal database error during seeding: %s", e)
            return

if __name__ == "__main__":
    main()