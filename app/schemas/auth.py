from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role_id: int  # Assign a default role upon registration


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    account_status: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role_id: Optional[int] = None
    account_status: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime