from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.models.role import Role
from app.core.dependencies import require_role_and_permission  # 📌 ប្រើប្រាស់ Composite Dependency
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserRoleAssign
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User & Role Management"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "user.create"))
):
    """
    Create a new user account in the system.
    - **Security**: Requires Admin role and 'user:create' permission.
    - **Validations**: Checks for duplicate email/username and hashes the password securely via UserService.
    """
    return UserService.create_user(db, payload)

# ១. អានបញ្ជី User ទាំងអស់ (Admin only + user:read permission)
@router.get("/", response_model=List[UserResponse], status_code=status.HTTP_200_OK)
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "user.read"))
):
    """Get all system users (Admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


# ២. អានព័ត៌មាន User ម្នាក់តាម ID (Admin only + user:read permission)
@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "user.read"))
):
    """Get user details by ID (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ៣. កែប្រែព័ត៌មាន User (Admin only + user:update permission)
@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "user.update"))
):
    """Update user information like username, email, or status (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.username is not None:
        user.username = payload.username
    if payload.email is not None:
        user.email = payload.email
    if payload.account_status is not None:
        user.account_status = payload.account_status
        
    db.commit()
    db.refresh(user)
    return user


# ៤. កែប្រែ ឬ Assign Role ឱ្យ User (Admin only + user:assign_role permission)
@router.put("/{user_id}/role", status_code=status.HTTP_200_OK)
def assign_role_to_user(
    user_id: int,
    payload: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "user.assign_role"))
):
    """Assign or change role for a specific user (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    user.role_id = payload.role_id
    db.commit()
    
    return {
        "message": f"Successfully assigned role '{role.name}' to user '{user.username}'",
        "user_id": user.id,
        "assigned_role_id": role.id
    }


# ៥. លុប User ចេញពីប្រព័ន្ធ (Admin only + user:delete permission)
@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin"], "user.delete"))
):
    """Delete a user from the system (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message": f"User with ID {user_id} deleted successfully"}