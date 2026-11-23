from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserUpdate,
    UserResponse,
)
from fastapi.security import OAuth2PasswordRequestForm  # 📌 នាំចូល Form នេះ
from app.core.security import get_password_hash, verify_password, create_access_token

from app.core.dependencies import get_current_user, require_permission, require_roles
from app.services.student_auth_service import StudentAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
        payload: UserRegister, 
        db: Session = Depends(get_db),
        user_by_role: User = Depends(require_roles(["Admin", "Teacher"])),  # ពិនិត្យ Role
        current_user: User = Depends(require_permission("user:create"))  #ពិនិត្យ Permission
    ):
    role = db.query(Role).filter(Role.id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == payload.email) | (User.username == payload.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or Username already registered.")

    new_user = User(
        username=payload.username,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        account_status="active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.add(UserRole(user_id=new_user.id, role_id=payload.role_id))
    db.commit()
    return {"message": "User registered successfully", "user_id": new_user.id}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # 📌 ប្រើប្រាស់ Form ជំនួស JSON Payload
    db: Session = Depends(get_db)
):
    # OAuth2PasswordRequestForm ប្រើប្រាស់ field 'username' (ដែលយើងអាចបញ្ចូល Email ឬ Username ក៏បាន)
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.account_status != "active":
        raise HTTPException(status_code=403, detail="Account is disabled.")

    # បង្កើត Token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "account_status": current_user.account_status,
        },
        "roles": [role.name for role in current_user.roles],
        "permissions": sorted({
            permission.name
            for role in current_user.roles
            for permission in role.permissions
        }),
    }


@router.get("/users", response_model=List[UserResponse])
def list_users(
        db: Session = Depends(get_db),
        user_by_role: User = Depends(require_roles(["Admin", "Teacher"])),  # ពិនិត្យ Role
        current_user: User = Depends(require_permission("user:read"))  #ពិនិត្យ Permission
    ):
    return db.query(User).all()


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    user_by_role: User = Depends(require_roles(["Admin", "Teacher"])),  # ពិនិត្យ Role
    current_user: User = Depends(require_permission("user:read"))  #ពិនិត្យ Permission
    ):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, 
    payload: UserUpdate, 
    db: Session = Depends(get_db),
    user_by_role: User = Depends(require_roles(["Admin", "Teacher"])),  # ពិនិត្យ Role
    current_user: User = Depends(require_permission("user:update"))  #ពិនិត្យ Permission
    ):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    updates = payload.model_dump(exclude_unset=True)
    if "password" in updates:
        updates["password_hash"] = get_password_hash(updates.pop("password"))

    if "role_id" in updates:
        role = db.query(Role).filter(Role.id == updates["role_id"]).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found.")
        role_id = updates.pop("role_id")
    else:
        role_id = None

    if "account_status" in updates and updates["account_status"] not in {"active", "disabled"}:
        raise HTTPException(
            status_code=400,
            detail="account_status must be 'active' or 'disabled'.",
        )

    if "email" in updates:
        existing = db.query(User).filter(
            User.email == str(updates["email"]),
            User.id != user_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered.")

    if "username" in updates:
        existing = db.query(User).filter(
            User.username == updates["username"],
            User.id != user_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered.")

    for field, value in updates.items():
        setattr(user, field, str(value) if field == "email" else value)

    db.commit()

    if role_id is not None:
        db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        db.add(UserRole(user_id=user_id, role_id=role_id))
        db.commit()

    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    user_by_role: User = Depends(require_roles(["Admin"])),  # ពិនិត្យ Role
    current_user: User = Depends(require_permission("user:create"))  #ពិនិត្យ Permission
    ):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully", "user_id": user_id}

