from typing import List

from fastapi import Depends, HTTPException, status
from app.database.session import get_db
from app.models.role import Role
from app.models.user import User
# Assumes get_current_user is already in this file or imported properly
from app.core.security import verify_password # (or wherever your auth dependency resides)

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.permission import Permission
from app.models.role_permissions import RolePermission
# from app.core.dependencies import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def require_roles(allowed_roles: List[str]):
    """Dependency សម្រាប់ពិនិត្យតួនាទី (Roles) របស់ User មុនអនុញ្ញាតឱ្យចូលប្រើ API"""
    def role_dependency(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # ពិនិត្យមើលថា User មាន Role ភ្ជាប់មកជាមួយដែរឬទេ
        if not current_user.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No role assigned to this user."
            )
        
        # ទាញយកឈ្មោះ Role ពី Database មកផ្ទៀងផ្ទាត់
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        if not role or role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_dependency

def require_permission(required_permission_code: str):
    """Dependency សម្រាប់ពិនិត្យសិទ្ធិ (Permission) របស់អ្នកប្រើប្រាស់"""
    def permission_dependency(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        # ប្រសិនបើ User គ្មាន Role ទេ មិនមានសិទ្ធិចូលប្រើ
        if not current_user.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: No role assigned to user."
            )
        
        # ពិនិត្យមើលថាតើ Role របស់ User មាន Permission នេះដែរឬទេ
        has_permission = db.query(RolePermission).join(
            Permission, RolePermission.permission_id == Permission.id
        ).filter(
            RolePermission.role_id == current_user.role_id,
            Permission.name == required_permission_code
        ).first()

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires permission '{required_permission_code}'."
            )
        return current_user
    return permission_dependency

def require_role_and_permission(allowed_roles: list[str], permission_code: str):
    """ពិនិត្យទាំង Role និង Permission ក្នុងពេលដំណាលគ្នា"""
    def dependency(
        user_role: User = Depends(require_roles(allowed_roles)),
        user_perm: User = Depends(require_permission(permission_code))
    ):
        return user_perm
    return dependency

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # 🔧 កែតម្រូវ៖ បម្លែង string 'sub' ត្រឡប់ទៅជា int វិញ ដើម្បី సరిសមជាមួយ Database ID
        user_id = int(user_id_str)
        
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    if user.account_status != "active":
        raise HTTPException(status_code=403, detail="Account is disabled.")
        
    return user