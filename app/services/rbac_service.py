from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import text
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.schemas.rbac import RoleCreate, PermissionBase


class RBACService:
    @staticmethod
    def create_permission(db: Session, payload: PermissionBase) -> Permission:
        existing = db.query(Permission).filter(Permission.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exists.")
        
        perm = Permission(name=payload.name, description=payload.description)
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm

    @staticmethod
    def get_all_permissions(db: Session):
        return db.query(Permission).all()

    @staticmethod
    def create_role(db: Session, payload: RoleCreate) -> Role:
        existing_role = db.query(Role).filter(Role.name == payload.name).first()
        if existing_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists.")
        
        new_role = Role(name=payload.name, status=payload.status, description=payload.description)
        
        if payload.permission_ids:
            perms = db.query(Permission).filter(Permission.id.in_(payload.permission_ids)).all()
            new_role.permissions = perms

        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        return new_role

    @staticmethod
    def get_all_roles(db: Session):
        return db.query(Role).all()

    @staticmethod
    def assign_role_to_user(db: Session, user_id: int, role_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        role = db.query(Role).filter(Role.id == role_id).first()

        if not user or not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or Role not found.")

        try:
            db.execute(
                text("INSERT INTO user_roles (user_id, role_id) VALUES (:uid, :rid)"),
                {"uid": user_id, "rid": role_id}
            )
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="User already has this role assigned."
            )

        return {"message": f"Successfully assigned role '{role.name}' to user '{user.username}'."}