import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.license_key import LicenseKey
from app.models.license_key_redemption import LicenseKeyRedemption
from app.schemas.license_key import LicenseKeyCreate
from app.models.user import User

class LicenseKeyService:

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        """Helper method to generate SHA-256 hash of the license key."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def create_license_key(db: Session, payload: LicenseKeyCreate, current_user: User) -> dict:
        """Create a new license key (C - Create)."""
        key_hash = LicenseKeyService._hash_key(payload.raw_key)
        key_prefix = payload.raw_key[:6]

        existing = db.query(LicenseKey).filter(LicenseKey.key_hash == key_hash).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This license key already exists in the system."
            )

        try:
            db_key = LicenseKey(
                key_hash=key_hash,
                key_prefix=key_prefix,
                created_by=current_user.id,
                max_uses=payload.max_uses,
                used_count=0,
                status="active",
                expires_at=payload.expires_at,
                description=payload.description
            )
            db.add(db_key)
            db.commit()
            db.refresh(db_key)

            return {
                "message": "License key created successfully.",
                "raw_key": payload.raw_key,  # បង្ហាញម្ដងគត់ពេលสร้าง
                "license_key": db_key
            }

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error while creating license key."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    @staticmethod
    def get_all_keys(db: Session, skip: int = 0, limit: int = 100) -> List[LicenseKey]:
        """Retrieve all license keys with pagination (R - Read All)."""
        try:
            return db.query(LicenseKey).offset(skip).limit(limit).all()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve license keys."
            )

    @staticmethod
    def get_key_by_id(db: Session, key_id: int) -> LicenseKey:
        """Retrieve a single license key by ID (R - Read By ID)."""
        key_obj = db.query(LicenseKey).filter(LicenseKey.id == key_id).first()
        if not key_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"License key with ID {key_id} not found."
            )
        return key_obj

    @staticmethod
    def update_license_key(db: Session, key_id: int, payload: dict) -> LicenseKey:
        """Update license key details like description, max_uses, or status (U - Update)."""
        key_obj = LicenseKeyService.get_key_by_id(db, key_id)

        try:
            if "max_uses" in payload and payload["max_uses"] is not None:
                if payload["max_uses"] < key_obj.used_count:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot set max_uses lower than the current used_count."
                    )
                key_obj.max_uses = payload["max_uses"]

            if "status" in payload and payload["status"] is not None:
                if payload["status"] not in ['active', 'revoked', 'expired']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid status value."
                    )
                key_obj.status = payload["status"]
                if payload["status"] == "revoked" and not key_obj.revoked_at:
                    key_obj.revoked_at = datetime.now()

            if "expires_at" in payload:
                key_obj.expires_at = payload["expires_at"]

            if "description" in payload:
                key_obj.description = payload["description"]

            db.commit()
            db.refresh(key_obj)
            return key_obj

        except HTTPException as he:
            raise he
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database error during license key update."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update license key: {str(e)}"
            )

    @staticmethod
    def revoke_license_key(db: Session, key_id: int) -> dict:
        """Specific helper to revoke a license key."""
        key_obj = LicenseKeyService.get_key_by_id(db, key_id)

        try:
            key_obj.status = "revoked"
            key_obj.revoked_at = datetime.now()
            db.commit()
            return {"message": f"License key ID {key_id} has been revoked successfully."}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke license key."
            )

    @staticmethod
    def delete_license_key(db: Session, key_id: int) -> dict:
        """Delete a license key from the system (D - Delete)."""
        key_obj = LicenseKeyService.get_key_by_id(db, key_id)

        try:
            db.delete(key_obj)
            db.commit()
            return {"message": f"License key with ID {key_id} deleted successfully."}
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete this license key because it has associated redemptions (restricted by foreign key)."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete license key: {str(e)}"
            )

    @staticmethod
    def redeem_license_key(db: Session, raw_key: str, current_user: User) -> dict:
        """Redeem a license key logic."""
        key_hash = LicenseKeyService._hash_key(raw_key)
        key_obj = db.query(LicenseKey).filter(LicenseKey.key_hash == key_hash).first()

        if not key_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid license key."
            )

        if key_obj.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"License key is not active (Status: {key_obj.status})."
            )

        if key_obj.expires_at and key_obj.expires_at < datetime.now():
            key_obj.status = "expired"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License key has expired."
            )

        if key_obj.used_count >= key_obj.max_uses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License key usage limit has been reached."
            )

        try:
            redemption = LicenseKeyRedemption(
                license_key_id=key_obj.id,
                user_id=current_user.id
            )
            db.add(redemption)

            key_obj.used_count += 1
            if key_obj.used_count >= key_obj.max_uses:
                key_obj.status = "expired"

            db.commit()
            return {"message": "License key redeemed successfully!"}

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already redeemed this key or a database conflict occurred."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Redemption failed: {str(e)}"
            )