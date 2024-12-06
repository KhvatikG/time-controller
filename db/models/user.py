import enum

from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.orm import Mapped
from sqlalchemy import String

from .base import Base


class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role='{self.role.value}')>"
