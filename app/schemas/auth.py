from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


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

class StudentSetupProfileSchema(BaseModel):
    # User Account Info
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    raw_key: str = Field(..., description="License key provided by teacher or admin")
    
    # Student Profile Info (ស្របតាម Model StudentProfile)
    student_id: str = Field(..., description="University student ID card number")
    full_name: str = Field(..., description="Student's full name")
    gender: Optional[str] = Field(None, description="Male, Female, or Other")
    date_of_birth: Optional[date] = None
    
    department: Optional[str] = None
    major: Optional[str] = None
    academic_year: Optional[str] = None
    class_name: Optional[str] = None
    
    phone: Optional[str] = None
    address: Optional[str] = None