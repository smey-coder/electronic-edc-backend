from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import StudentSetupProfileSchema
from app.services.student_auth_service import StudentAuthService

router = APIRouter(prefix="/students", tags=["Student Self-Registration"])

@router.post("/register-with-key", status_code=status.HTTP_201_CREATED)
def register_student_with_license_key(
    payload: StudentSetupProfileSchema,
    db: Session = Depends(get_db)
):
    """
    For New Students: Register a student account by verifying and redeeming a valid license key.
    After successful registration, students can log in normally via /auth/login (Email & Password).
    """
    return StudentAuthService.setup_student_profile_with_key(db, payload)