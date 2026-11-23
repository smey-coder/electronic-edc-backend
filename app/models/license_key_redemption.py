from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, BigInteger, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class LicenseKeyRedemption(Base):
    __tablename__ = "license_key_redemptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, index=True)
    license_key_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("license_keys.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("license_key_id", "user_id", name="uq_license_key_user"),
    )

    # Relationships
    license_key = relationship("LicenseKey", back_populates="redemptions")
    user = relationship("User", backref="redeemed_keys")