from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, BigInteger, Text, Date, DateTime, Boolean, CheckConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    student_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    major: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    academic_year: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    class_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    __table_args__ = (
        CheckConstraint("gender IS NULL OR gender IN ('Male', 'Female', 'Other')", name="chk_gender"),
    )

    # Relationship ជាមួយ User model
    user: Mapped["User"] = relationship("User", back_populates="student_profile")