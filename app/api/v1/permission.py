from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.core.dependencies import require_role_and_permission
from app.schemas.permission import PermissionCreate, PermissionUpdate, PermissionResponse
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permission Management"])


@router.post("/", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "permission.create"))
):
    """Create a new system permission (Admin only)."""
    return PermissionService.create_permission(db, payload)


@router.get("/", response_model=List[PermissionResponse], status_code=status.HTTP_200_OK)
def get_all_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "permission.read"))
):
    """Get all permissions (Admin only)."""
    return PermissionService.get_all_permissions(db, skip=skip, limit=limit)


@router.get("/{perm_id}", response_model=PermissionResponse, status_code=status.HTTP_200_OK)
def get_permission_by_id(
    perm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "permission.read"))
):
    """Get permission details by ID (Admin only)."""
    return PermissionService.get_permission_by_id(db, perm_id)


@router.put("/{perm_id}", response_model=PermissionResponse, status_code=status.HTTP_200_OK)
def update_permission(
    perm_id: int,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "permission.update"))
):
    """Update permission information (Admin only)."""
    return PermissionService.update_permission(db, perm_id, payload)


@router.delete("/{perm_id}", status_code=status.HTTP_200_OK)
def delete_permission(
    perm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "permission.delete"))
):
    """Delete a permission from the system (Admin only)."""
    return PermissionService.delete_permission(db, perm_id)