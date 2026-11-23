from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.schemas.rbac import (
    RoleCreate, RoleResponse, 
    PermissionBase, PermissionResponse, 
    UserRoleAssign
)
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/rbac", tags=["Role-Based Access Control"])


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
def create_permission(payload: PermissionBase, db: Session = Depends(get_db)):
    return RBACService.create_permission(db, payload)


@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(db: Session = Depends(get_db)):
    return RBACService.get_all_permissions(db)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)):
    return RBACService.create_role(db, payload)


@router.get("/roles", response_model=List[RoleResponse])
def list_roles(db: Session = Depends(get_db)):
    return RBACService.get_all_roles(db)


@router.post("/assign-role", status_code=status.HTTP_200_OK)
def assign_role(payload: UserRoleAssign, db: Session = Depends(get_db)):
    return RBACService.assign_role_to_user(db, payload.user_id, payload.role_id)