"""Persistence for roles."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role, RoleName


def get_by_name(db: Session, name: RoleName) -> Role | None:
    return db.scalar(select(Role).where(Role.name == name))


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name)))
