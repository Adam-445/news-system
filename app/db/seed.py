from sqlalchemy.orm import Session
from app.db.database import engine
from app.db.models import Role
from app.db.models import Permission

def seed_roles_permissions():
    session = Session(bind=engine)
    try:
        # Define default roles
        default_roles = [
            Role(name="admin", description="Administrator with full access."),
            Role(name="moderator", description="Moderator with limited management access."),
            Role(name="regular", description="Regular user with basic access."),
        ]
        for role in default_roles:
            if not session.query(Role).filter_by(name=role.name).first():
                session.add(role)

        # Define default permissions
        default_permissions = [
            Permission(name="create_article", description="Can create articles."),
            Permission(name="delete_article", description="Can delete articles."),
            Permission(name="update_article", description="Can update articles."),
            Permission(name="delete_user", description="Can delete users."),
        ]
        for perm in default_permissions:
            if not session.query(Permission).filter_by(name=perm.name).first():
                session.add(perm)

        # Assign permissions to roles.
        admin = session.query(Role).filter_by(name="admin").first()
        moderator = session.query(Role).filter_by(name="moderator").first()
        regular = session.query(Role).filter_by(name="regular").first()

        if admin and not admin.permissions:
            admin.permissions.extend(default_permissions)
        if moderator and not moderator.permissions:
            # Give moderator a subset of permissions
            moderator.permissions.extend(
                [perm for perm in default_permissions if perm.name != "delete_user"]
            )

        session.commit()
    except Exception as e:
        session.rollback()
        print("Error seeding data:", e)
    finally:
        session.close()

if __name__ == "__main__":
    seed_roles_permissions()
