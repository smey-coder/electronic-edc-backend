from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role_and_permission  # ប្តូរ path បើ get_db នៅកន្លែងផ្សេង
from app.models.user import User
from app.schemas.settings import ProfileUpdateSchema, PasswordChangeSchema
from app.services.settings_service import SettingsService as S

router = APIRouter(prefix="/me", tags=["Account settings"])

# គ្រប់ role ដែលអាចប្រើ Settings
ALL_ROLES = ["Admin", "Teacher", "Student"]


@router.get("/profile")
def get_profile(
    current_user: User = Depends(require_role_and_permission(ALL_ROLES, "profile.show")),
):
    return S.serialize(current_user)


@router.put("/profile")
def update_profile(
    body: ProfileUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(ALL_ROLES, "profile.update")),
):
    return S.update_profile(db, current_user, body)


@router.post("/password")
def change_password(
    body: PasswordChangeSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(ALL_ROLES, "password.update")),
):
    return S.change_password(db, current_user, body)