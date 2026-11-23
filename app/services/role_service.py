from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permissions import RolePermission
from app.schemas.role import RoleCreate, RoleUpdate

class RoleService:

    @staticmethod
    def create_role(db: Session, payload: RoleCreate) -> Role:
        # ពិនិត្យមើលឈ្មោះ Role ជាន់គ្នា
        existing_role = db.query(Role).filter(Role.name == payload.name).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{payload.name}' already exists."
            )

        try:
            # ១. បង្កើត Role Object
            db_role = Role(
                name=payload.name,
                description=payload.description
            )
            db.add(db_role)
            db.commit()
            db.refresh(db_role)

            # ២. ភ្ជាប់ Permissions (បើមានการជ្រើសរើស Checkbox)
            if payload.permission_ids:
                for perm_id in payload.permission_ids:
                    perm_exists = db.query(Permission).filter(Permission.id == perm_id).first()
                    if perm_exists:
                        role_perm = RolePermission(role_id=db_role.id, permission_id=perm_id)
                        db.add(role_perm)
                db.commit()

            # 3. Formulate response with permission IDs
            setattr(db_role, "permissions", [p.permission_id for p in db.query(RolePermission).filter(RolePermission.role_id == db_role.id).all()])
            return db_role

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error while creating role."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    @staticmethod
    def get_all_roles(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        try:
            roles = db.query(Role).offset(skip).limit(limit).all()
            result = []
            for r in roles:
                perm_ids = [p.permission_id for p in db.query(RolePermission).filter(RolePermission.role_id == r.id).all()]
                result.append({
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "permissions": perm_ids
                })
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve roles."
            )

    @staticmethod
    def get_role_by_id(db: Session, role_id: int) -> dict:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found."
            )
        perm_ids = [p.permission_id for p in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()]
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": perm_ids
        }

    @staticmethod
    def update_role(db: Session, role_id: int, payload: RoleUpdate) -> dict:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        try:
            if payload.name is not None:
                duplicate = db.query(Role).filter(Role.name == payload.name, Role.id != role_id).first()
                if duplicate:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Role name '{payload.name}' is already taken."
                    )
                role.name = payload.name

            if payload.description is not None:
                role.description = payload.description

            # កែប្រែ ឬ Update Checkbox Permissions (លុបសិទ្ធិចាស់ចោល រួច Insert សិទ្ធិថ្មីដែលបាន Tick)
            if payload.permission_ids is not None:
                db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
                for perm_id in payload.permission_ids:
                    perm_exists = db.query(Permission).filter(Permission.id == perm_id).first()
                    if perm_exists:
                        role_perm = RolePermission(role_id=role_id, permission_id=perm_id)
                        db.add(role_perm)

            db.commit()
            db.refresh(role)

            perm_ids = [p.permission_id for p in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()]
            return {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": perm_ids
            }
        except HTTPException as he:
            raise he
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database error during role update."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role."
            )

    @staticmethod
    def delete_role(db: Session, role_id: int) -> dict:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        try:
            # លុប RolePermissions មុននឹងលុប Role (ដើម្បីការពារ Foreign Key Conflict)
            db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
            db.delete(role)
            db.commit()
            return {"message": f"Role with ID {role_id} deleted successfully."}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role."
            )