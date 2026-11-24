from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class ProfileUpdateSchema(BaseModel):
    # វាលរបស់គណនី (users) — Admin/Teacher/Student ប្រើ email បាន
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None

    # វាលរបស់ Student Profile (student_profiles) — សម្រាប់តែ Student
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    gender: Optional[str] = None            # Male | Female | Other (ត្រូវនឹង chk_gender)
    date_of_birth: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=30)   # ត្រូវនឹង String(30)
    address: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def valid_gender(cls, v):
        if v is not None and v not in ("Male", "Female", "Other"):
            raise ValueError("Gender must be Male, Female or Other.")
        return v


class PasswordChangeSchema(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v):
        if not (any(c.isalpha() for c in v) and any(c.isdigit() for c in v)):
            raise ValueError("Password must contain letters and numbers.")
        return v