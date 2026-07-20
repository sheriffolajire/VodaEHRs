"""Idempotent seeding of roles and the initial admin account.

Run after migrations:  python -m app.seed
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.crypto.hashing import hash_password
from app.database.session import SessionLocal
from app.models.role import Role, RoleName
from app.models.user import User
from app.repositories import role_repository, user_repository

logger = get_logger("application")


def seed_roles(db: Session) -> None:
    """Insert any missing roles. Safe to run repeatedly."""
    for role_name in RoleName:
        if role_repository.get_by_name(db, role_name) is None:
            db.add(Role(name=role_name))
    db.flush()


def seed_admin(db: Session) -> None:
    """Create the initial admin account if it does not already exist."""
    if user_repository.get_by_email(db, settings.initial_admin_email) is not None:
        return

    admin_role = role_repository.get_by_name(db, RoleName.ADMIN)
    if admin_role is None:
        raise RuntimeError("Admin role missing; seed roles before the admin user.")

    db.add(
        User(
            first_name=settings.initial_admin_first_name,
            last_name=settings.initial_admin_last_name,
            email=settings.initial_admin_email,
            password_hash=hash_password(settings.initial_admin_password),
            role_id=admin_role.id,
        )
    )


def main() -> None:
    configure_logging()
    db = SessionLocal()
    try:
        seed_roles(db)
        seed_admin(db)
        db.commit()
        logger.info("Seed complete: roles and initial admin ensured.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
