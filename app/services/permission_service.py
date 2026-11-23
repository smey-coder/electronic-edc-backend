from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List

from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

class PermissionService:

    @staticmethod
    def create_permission(db: Session, payload: PermissionCreate) -> Permission:
        # ពិនិត្យមើលថាតើ Permission Name មានរួចហើយឬยัง
        existing_perm = db.query(Permission).filter(Permission.name == payload.name).first()
        if existing_perm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Permission with name '{payload.name}' already exists."
            )

        try:
            db_perm = Permission(
                name=payload.name,
                description=payload.description
            )
            db.add(db_perm)
            db.commit()
            db.refresh(db_perm)
            return db_perm
            
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error while creating permission."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    @staticmethod
    def get_all_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
        try:
            return db.query(Permission).offset(skip).limit(limit).all()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve permissions."
            )

    @staticmethod
    def get_permission_by_id(db: Session, perm_id: int) -> Permission:
        perm = db.query(Permission).filter(Permission.id == perm_id).first()
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission with ID {perm_id} not found."
            )
        return perm

    @staticmethod
    def update_permission(db: Session, perm_id: int, payload: PermissionUpdate) -> Permission:
        perm = PermissionService.get_permission_by_id(db, perm_id)

        try:
            if payload.name is not None:
                # ពិនិត្យឈ្មោះซ้ำពេល Update
                duplicate = db.query(Permission).filter(Permission.name == payload.name, Permission.id != perm_id).first()
                if duplicate:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Permission name '{payload.name}' is already taken."
                    )
                perm.name = payload.name

            if payload.description is not None:
                perm.description = payload.description

            db.commit()
            db.refresh(perm)
            return perm
            
        except HTTPException as he:
            raise he
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database error during permission update."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update permission."
            )

    @staticmethod
    def delete_permission(db: Session, perm_id: int) -> dict:
        perm = PermissionService.get_permission_by_id(db, perm_id)

        try:
            db.delete(perm)
            db.commit()
            return {"message": f"Permission with ID {perm_id} deleted successfully."}
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete this permission because it is currently assigned to roles."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete permission."
            )