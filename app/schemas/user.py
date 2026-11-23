from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role_id: Optional[int] = None  # ID របស់ Role ដែលត្រូវកំណត់ឱ្យពេលបង្កើត User ថ្មី

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    account_status: Optional[str] = None  # active, disabled, etc.

class UserRoleAssign(BaseModel):
    role_id: int  # ID របស់ Role ដែលត្រូវ Assign ឱ្យ User នេះ
    
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    account_status: str
    role_id: Optional[int] = None

    class Config:
        from_attributes = True