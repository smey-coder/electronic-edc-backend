import hashlib
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.user import User
from app.models.license_key import LicenseKey
from app.models.license_key_redemption import LicenseKeyRedemption
from app.models.student_profile import StudentProfile
from app.schemas.auth import StudentSetupProfileSchema
from app.core.security import get_password_hash
from app.models.user_role import UserRole
from app.services.license_access_service import get_license_access

class StudentAuthService:

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def setup_student_profile_with_key(db: Session, payload: StudentSetupProfileSchema) -> dict:
        # ១. ផ្ទៀងផ្ទាត់ License Key
        key_hash = StudentAuthService._hash_key(payload.raw_key)
        license_key = db.query(LicenseKey).filter(LicenseKey.key_hash == key_hash).first()

        if not license_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid license key provided."
            )

        if license_key.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"License key is not active (Status: {license_key.status})."
            )

        # ពិនិត្យថ្ងៃខែផុតកំណត់ (Naive datetime comparison)
        if license_key.expires_at and license_key.expires_at < datetime.now():
            license_key.status = "expired"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License key has expired."
            )

        if license_key.used_count >= license_key.max_uses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License key usage limit has already been reached."
            )

        # ២. ឆែកមើល Email ឬ Username ជាន់គ្នា
        if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username is already registered."
            )

        # ៣. ឆែកមើល student_id ជាន់គ្នា
        existing_student_id = db.query(StudentProfile).filter(StudentProfile.student_id == payload.student_id).first()
        if existing_student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID is already registered in the system."
            )

        try:
            # ៤. បង្កើត User Account ថ្មី (ដក role_id ออก ព្រោះ UserRole table)
            hashed_password = get_password_hash(payload.password)
            
            new_user = User(
                username=payload.username,
                email=payload.email,
                password_hash=hashed_password,
                account_status="active"
            )
            db.add(new_user)
            db.flush() # 📌 បង្កើត User រួច flush ដើម្បីទាញយក new_user.id យកមកប្រើប្រាស់ຕໍ່

            # ៥. 🔗 ភ្ជាប់ Role (Student Role ID = 2) ຜ່ານ UserRole table ຢ່າງត្រឹមត្រូវ
            STUDENT_ROLE_ID = 2  
            db.add(UserRole(user_id=new_user.id, role_id=STUDENT_ROLE_ID))

            # ៦. 🔗 បង្កើត Student Profile ស្របតាម Model របស់អ្នក
            student_profile = StudentProfile(
                user_id=new_user.id,
                student_id=payload.student_id,
                full_name=payload.full_name,
                gender=payload.gender,
                date_of_birth=payload.date_of_birth,
                department=payload.department,
                major=payload.major,
                academic_year=payload.academic_year,
                class_name=payload.class_name,
                phone=payload.phone,
                address=payload.address,
                profile_completed=True,
                profile_completed_at=datetime.now()
            )
            db.add(student_profile)

            # ៧. កត់ត្រាการ Redeem License Key
            redemption = LicenseKeyRedemption(
                license_key_id=license_key.id,
                user_id=new_user.id
            )
            db.add(redemption)

            # ៨. កើនចំនួន used_count របស់ Key
            license_key.used_count += 1
            if license_key.used_count >= license_key.max_uses:
                license_key.status = "expired"

            # Commit ទិន្នន័យទាំងអស់ក្នុង Transaction តែមួយ (Atomicity)
            db.commit()
            db.refresh(new_user)

            return {
                "message": "Student account setup and license key redemption completed successfully!",
                "user_id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "student_id": payload.student_id,
                "full_name": payload.full_name
            }

        except IntegrityError as ie:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database integrity error: {str(ie)}"
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Student profile setup failed: {str(e)}"
            )

    # service
    @staticmethod
    def redeem_for_existing_user(db: Session, user: User, raw_key: str) -> dict:
        key_hash = StudentAuthService._hash_key(raw_key)
        key = db.query(LicenseKey).filter(LicenseKey.key_hash == key_hash).first()
        if not key:
            raise HTTPException(404, "Invalid license key provided.")
        if key.status != "active":
            raise HTTPException(400, f"License key is not active (Status: {key.status}).")
        if key.expires_at and key.expires_at < datetime.now():
            key.status = "expired"
            db.commit()
            raise HTTPException(400, "License key has expired.")
        if key.used_count >= key.max_uses:
            raise HTTPException(400, "License key usage limit has already been reached.")
        if db.query(LicenseKeyRedemption).filter_by(license_key_id=key.id, user_id=user.id).first():
            raise HTTPException(400, "You have already used this key.")

        db.add(LicenseKeyRedemption(license_key_id=key.id, user_id=user.id))
        key.used_count += 1
        db.commit()
        return get_license_access(db, user)