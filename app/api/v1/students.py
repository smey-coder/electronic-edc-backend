from fastapi import APIRouter, Depends, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.schemas.student import (
    StudentProfileCreate, 
    StudentProfileUpdate, 
    StudentProfileResponse
)
from app.services.student_service import StudentService
from app.core.dependencies import get_current_user
from app.core.dependencies import require_permission 
from app.core.dependencies import require_roles
from app.core.dependencies import require_role_and_permission
from app.models.user import User

router = APIRouter(prefix="/students", tags=["Student Management & RBAC"])


@router.post("/", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
def create_student_profile(
    payload: StudentProfileCreate, 
    db: Session = Depends(get_db),
    #version1
    # user_by_role: User = Depends(require_roles(["Admin", "Teacher"])),  # ពិនិត្យ Role
    # current_user: User = Depends(require_permission("student:create"))  #ពិនិត្យ Permission
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "student.create"))
):
    """Create a single student profile (Requires 'student:create' permission)."""
    return StudentService.create_profile(db, payload)


@router.get("/", response_model=List[StudentProfileResponse], status_code=status.HTTP_200_OK)
def get_all_students(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=500), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "student.read"))
):
    """Read: ទាញយកបញ្ជីសិស្សទាំងអស់ (Requires 'student:read' permission)"""
    return StudentService.get_all_students(db, skip=skip, limit=limit)


@router.get("/{student_id}", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
def get_student_by_id(
    student_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "student.read"))
):
    """Read: ទាញយកព័ត៌មានលម្អិតរបស់សិស្សតាម ID"""
    return StudentService.get_student_by_id(db, student_id)


@router.put("/{student_id}", response_model=StudentProfileResponse, status_code=status.HTTP_200_OK)
def update_student(
    student_id: int, 
    payload: StudentProfileUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "student.update"))
):
    """Update: កែប្រែទិន្នន័យសិស្ស"""
    return StudentService.update_student(db, student_id, payload)


@router.delete("/{student_id}", status_code=status.HTTP_200_OK)
def delete_student(
    student_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "student.delete"))
):
    """Delete: លុបសិស្សចេញពីប្រព័ន្ធ"""
    return StudentService.delete_student(db, student_id)


@router.post("/import-excel", status_code=status.HTTP_200_OK)
def import_students_excel(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "student.import"))
):
    """Upload and import students in bulk using an Excel file."""
    return StudentService.import_students_from_excel(db, file)