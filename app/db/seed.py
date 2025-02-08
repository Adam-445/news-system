import os
from sqlalchemy.orm import Session

from app.db.database import engine
from app.db.models.role import Role
from app.db.models.permission import Permission
from app.db.models.user import User
from app.core import security
from app.core.config import settings


def seed_roles_permissions(session: Session, seed_default_users: bool = False):
    try:
        # Create default roles
        default_roles = [
            Role(name="admin", description="Administrator with full access."),
            Role(
                name="moderator",
                description="Moderator with limited management access.",
            ),
            Role(name="regular", description="Regular user with basic access."),
        ]
        for role in default_roles:
            if not session.query(Role).filter_by(name=role.name).first():
                session.add(role)

        # Create default permissions
        default_permissions = [
            Permission(name="create_article", description="Can create articles."),
            Permission(name="delete_article", description="Can delete articles."),
            Permission(name="update_article", description="Can update articles."),
            Permission(name="delete_user", description="Can delete users."),
        ]
        for perm in default_permissions:
            if not session.query(Permission).filter_by(name=perm.name).first():
                session.add(perm)

        # Flush the session so that roles and permissions exist in the DB.
        session.flush()

        # Assign permissions to roles.
        admin = session.query(Role).filter_by(name="admin").first()
        moderator = session.query(Role).filter_by(name="moderator").first()
        regular = session.query(Role).filter_by(name="regular").first()

        # Admin gets all permissions.
        if admin and not admin.permissions:
            admin.permissions.extend(session.query(Permission).all())
        # Moderator gets all permissions except "delete_user".
        if moderator and not moderator.permissions:
            moderator.permissions.extend(
                session.query(Permission).filter(Permission.name != "delete_user").all()
            )
        # Regular users have no special permissions.

        # Create default users for testing/demo.
        if seed_default_users:
            default_users = [
                User(
                    username="regular_user",
                    email="regular@example.com",
                    password=security.get_password_hash("TestPass123!"),
                    role_name="regular",
                ),
                User(
                    username="moderator_user",
                    email="moderator@example.com",
                    password=security.get_password_hash("TestPass123!"),
                    role_name="moderator",
                ),
                User(
                    username="admin_user",
                    email="admin@example.com",
                    password=security.get_password_hash("TestPass123!"),
                    role_name="admin",
                ),
            ]
            for user in default_users:
                if not session.query(User).filter_by(username=user.username).first():
                    session.add(user)

        session.commit()
    except Exception as e:
        session.rollback()
        print("Error seeding data:", e)
    finally:
        session.close()


if __name__ == "__main__":
    # Only run seeding in non-production environments
    env = settings.enviornment
    seed_users: bool = False
    if env == "development":
        seed_users = True
    else:
        print("Seeding default users skipped in production environment.")
    seed_roles_permissions(session=Session(bind=engine), seed_default_users=seed_users)
    print("Seeding successful.")
