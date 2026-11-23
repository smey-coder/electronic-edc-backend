from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List

from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserService:
    
    @staticmethod
    def create_user(db: Session, payload: UserCreate) -> User:
        # ១. ពិនិត្យមើល Email ជាន់គ្នា
        existing_email = db.query(User).filter(User.email == payload.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered."
            )
            
        # ២. ពិនិត្យមើល Username ជាន់គ្នា
        existing_username = db.query(User).filter(User.username == payload.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken."
            )

        try:
            # ៣. Hash Password មុនរក្សាទុក (ចំណាំ៖ មិនដាក់ role_id ក្នុង Constructor ទេ ព្រោះវាជា Property)
            hashed_password = get_password_hash(payload.password)
            
            db_user = User(
                username=payload.username,
                email=payload.email,
                password_hash=hashed_password,
                account_status="active"
            )
            
            # ៤.បញ្ជូន role_id មក ត្រូវ Append ចូលទៅក្នុង roles relationship (Many-to-Many)
            if payload.role_id:
                role = db.query(Role).filter(Role.id == payload.role_id).first()
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Role with ID {payload.role_id} not found."
                    )
                db_user.roles.append(role)
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
            
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error. Please check your input data."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        try:
            return db.query(User).offset(skip).limit(limit).all()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve users."
            )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found."
            )
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
        user = UserService.get_user_by_id(db, user_id)
        
        try:
            if payload.username is not None:
                user.username = payload.username
            if payload.email is not None:
                user.email = payload.email
            if payload.account_status is not None:
                user.account_status = payload.account_status
                
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email might already be taken by another user."
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile."
            )

    @staticmethod
    def assign_role(db: Session, user_id: int, role_id: int) -> User:
        user = UserService.get_user_by_id(db, user_id)
        
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found."
            )
            
        try:
            # 📌 ជំនួស Role ថ្មីចូលទៅក្នុង many-to-many relationship ( Role 主)
            user.roles = [role]
            
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role to user."
            )

    @staticmethod
    def delete_user(db: Session, user_id: int) -> dict:
        user = UserService.get_user_by_id(db, user_id)
        
        try:
            db.delete(user)
            db.commit()
            return {"message": f"User with ID {user_id} deleted successfully."}
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user."
            )