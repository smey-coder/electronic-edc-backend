from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, BigInteger, Text, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Enum('active', 'disabled', name="role_status_enum"), nullable=False, default="active")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationship ជាមួយ Permissions
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles"
    )