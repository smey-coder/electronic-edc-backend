from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LicenseKeyCreate(BaseModel):
    raw_key: str = Field(..., min_length=8, description="Plain text license key to be hashed")
    max_uses: int = Field(1, gt=0, description="Maximum allowed uses")
    expires_at: Optional[datetime] = Field(None, description="Expiration date and time")
    description: Optional[str] = Field(None, description="Optional notes")

class LicenseKeyResponse(BaseModel):
    id: int
    key_prefix: str
    created_by: int
    status: str
    max_uses: int
    used_count: int
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LicenseKeyVerify(BaseModel):
    raw_key: str = Field(..., description="Key provided by client to redeem/verify")


class LicenseKeyUpdate(BaseModel):
    max_uses: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, description="active, revoked, or expired")
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class RedeemKeySchema(BaseModel):
        raw_key: str