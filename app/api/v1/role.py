from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app.database.session import get_db
from app.models.user import User
from app.core.dependencies import require_role_and_permission
from app.schemas.role import RoleCreate, RoleUpdate, RoleResponse
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["Role Management"])


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "role.create"))
):
    """Create a new role with permissions checkboxes (Admin only)."""
    return RoleService.create_role(db, payload)


@router.get("/", response_model=List[RoleResponse], status_code=status.HTTP_200_OK)
def get_all_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "role.read"))
):
    """Get all roles along with their permission IDs (Admin only)."""
    return RoleService.get_all_roles(db, skip=skip, limit=limit)


@router.get("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
def get_role_by_id(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "role.read"))
):
    """Get role details and its permissions by ID (Admin only)."""
    return RoleService.get_role_by_id(db, role_id)


@router.put("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "role.update"))
):
    """Update role details and its assigned checkboxes/permissions (Admin only)."""
    return RoleService.update_role(db, role_id, payload)


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "role.delete"))
):
    """Delete a role and its permission mapping from the system (Admin only)."""
    return RoleService.delete_role(db, role_id)