from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.security import get_password_hash, verify_password
from app.schemas.settings import ProfileUpdateSchema, PasswordChangeSchema

# តួនាទីដែលមិនអាចកែ Student Profile
STAFF_ROLES = {"admin", "teacher"}

# វាលដែលជារបស់ student_profiles
STUDENT_FIELDS = {"full_name", "gender", "date_of_birth", "phone", "address"}


def _role_names(user: User) -> set[str]:
    # ប្តូរ `r.name` បើ column របស់ Role អ្នកមិនមែនឈ្មោះ name
    return {r.name.lower() for r in user.roles}


def is_staff(user: User) -> bool:
    return bool(_role_names(user) & STAFF_ROLES)


class SettingsService:

    # ---------- អាន Profile ----------
    @staticmethod
    def serialize(user: User) -> dict:
        staff = is_staff(user)
        data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "roles": sorted(_role_names(user)),
            "is_student": not staff,
        }
        profile = user.student_profile
        # ផ្ញើទិន្នន័យ Student តែនៅពេលមិនមែន staff និងមាន profile
        if profile and not staff:
            data.update({
                "student_id": profile.student_id,
                "full_name": profile.full_name,
                "gender": profile.gender,
                "date_of_birth": profile.date_of_birth,
                "phone": profile.phone,
                "address": profile.address,
                "photo_url": profile.profile_image,
                # ព័ត៌មានដែលសាលាគ្រប់គ្រង (បង្ហាញតែអាន)
                "department": profile.department,
                "major": profile.major,
                "academic_year": profile.academic_year,
                "class_name": profile.class_name,
            })
        return data

    # ---------- កែ Profile ----------
    @staticmethod
    def update_profile(db: Session, user: User, payload: ProfileUpdateSchema) -> dict:
        data = payload.model_dump(exclude_unset=True)
        staff = is_staff(user)

        # ១) ច្បាប់តាម role (ពិនិត្យមុនគេ មុនកែអ្វីទាំងអស់)
        if staff and (STUDENT_FIELDS & data.keys()):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Admins and teachers cannot edit student profiles.",
            )
        if not staff and "username" in data:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Students cannot change their username.",
            )

        # ២) កែគណនី users — email
        new_email = data.pop("email", None)
        if new_email and new_email != user.email:
            if db.query(User).filter(User.email == new_email, User.id != user.id).first():
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email is already in use.")
            user.email = new_email

        # ៣) កែគណនី users — username (តែ staff)
        new_username = data.pop("username", None)
        if new_username and new_username != user.username:
            if db.query(User).filter(User.username == new_username, User.id != user.id).first():
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username is already in use.")
            user.username = new_username

        # ៤) កែ student_profiles (តែ Student)
        if not staff:
            profile = user.student_profile
            if not profile:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Student profile not found.")
            for field, value in data.items():
                if field == "full_name" and value is None:
                    continue  # full_name ជា column ដែលចាំបាច់ មិនអាចលុបបាន
                setattr(profile, field, value)

        # ៥) រក្សាទុក
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not update profile.")

        db.refresh(user)
        return SettingsService.serialize(user)

    # ---------- ប្តូរពាក្យសម្ងាត់ ----------
    @staticmethod
    def change_password(db: Session, user: User, payload: PasswordChangeSchema) -> dict:
        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect.")
        if payload.current_password == payload.new_password:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "New password must be different.")

        user.password_hash = get_password_hash(payload.new_password)
        db.commit()
        return {"message": "Password changed successfully."}