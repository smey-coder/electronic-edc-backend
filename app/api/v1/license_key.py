from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.core.dependencies import require_role_and_permission, get_current_user
from app.schemas.license_key import (
    LicenseKeyCreate, 
    LicenseKeyUpdate, 
    LicenseKeyResponse, 
    LicenseKeyVerify
)
from app.services.license_key_service import LicenseKeyService

router = APIRouter(prefix="/license-keys", tags=["License Key Management"])

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_license_key(
    payload: LicenseKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "license.create"))
):
    """Create a new hashed license key (Admin only)."""
    return LicenseKeyService.create_license_key(db, payload, current_user)

@router.get("/", response_model=List[LicenseKeyResponse], status_code=status.HTTP_200_OK)
def get_all_license_keys(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "license.read"))
):
    """Get all system license keys with pagination (Admin only)."""
    return LicenseKeyService.get_all_keys(db, skip=skip, limit=limit)

@router.get("/{key_id}", response_model=LicenseKeyResponse, status_code=status.HTTP_200_OK)
def get_license_key_by_id(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "license.read"))
):
    """Get license key details by ID (Admin only)."""
    return LicenseKeyService.get_key_by_id(db, key_id)

@router.put("/{key_id}", response_model=LicenseKeyResponse, status_code=status.HTTP_200_OK)
def update_license_key(
    key_id: int,
    payload: LicenseKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "license.update"))
):
    """Update license key details like max_uses, status, or description (Admin only)."""
    return LicenseKeyService.update_license_key(db, key_id, payload.model_dump(exclude_unset=True))

@router.put("/{key_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_license_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "license.revoke"))
):
    """Revoke an active license key (Admin only)."""
    return LicenseKeyService.revoke_license_key(db, key_id)

@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
def delete_license_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "license.delete"))
):
    """Delete a license key from the system (Admin only)."""
    return LicenseKeyService.delete_license_key(db, key_id)

@router.post("/redeem", status_code=status.HTTP_200_OK)
def redeem_license_key(
    payload: LicenseKeyVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Redeem a license key for the currently authenticated user."""
    return LicenseKeyService.redeem_license_key(db, payload.raw_key, current_user)