from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import date, datetime


def normalize_gender(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value

    normalized = value.strip().title()
    if normalized not in {"Male", "Female", "Other"}:
        raise ValueError("gender must be Male, Female, or Other")
    return normalized


class StudentProfileBase(BaseModel):
    student_id: str
    full_name: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    department: Optional[str] = None
    major: Optional[str] = None
    academic_year: Optional[str] = None
    class_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        return normalize_gender(value)


class StudentProfileCreate(StudentProfileBase):
    user_id: int


class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    department: Optional[str] = None
    major: Optional[str] = None
    academic_year: Optional[str] = None
    class_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, value: Optional[str]) -> Optional[str]:
        return normalize_gender(value)


class StudentProfileResponse(StudentProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    profile_completed: bool
    profile_completed_at: Optional[datetime] = None
    created_at: datetime