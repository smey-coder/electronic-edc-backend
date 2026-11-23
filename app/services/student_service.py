import io
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status, UploadFile
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.student import StudentProfileCreate, StudentProfileUpdate


class StudentService:
    @staticmethod
    def create_profile(db: Session, payload: StudentProfileCreate):
        # ពិនិត្យមើល User ថាមានមែនឬអត់
        user = db.query(User).filter(User.id == payload.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        existing = db.query(StudentProfile).filter(StudentProfile.student_id == payload.student_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student ID already exists.")

        existing_profile = db.query(StudentProfile).filter(
            StudentProfile.user_id == payload.user_id
        ).first()
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a student profile.",
            )

        profile = StudentProfile(
            user_id=payload.user_id,
            student_id=payload.student_id,
            full_name=payload.full_name,
            gender=payload.gender,
            date_of_birth=payload.date_of_birth,
            department=payload.department,
            major=payload.major,
            academic_year=payload.academic_year,
            class_name=payload.class_name,
            phone=payload.phone,
            address=payload.address,
            profile_completed=True,
            profile_completed_at=pd.Timestamp.now()
        )
        db.add(profile)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student profile conflicts with existing data.",
            ) from exc
        db.refresh(profile)
        return profile

    @staticmethod
    def get_all_students(db: Session, skip: int = 0, limit: int = 100):
        """Read: ទាញយកបញ្ជីសិស្សទាំងអស់ (មាន pagination)"""
        return db.query(StudentProfile).offset(skip).limit(limit).all()

    @staticmethod
    def get_student_by_id(db: Session, student_id: int):
        """Read: ទាញយកព័ត៌មានសិស្សតាម ID"""
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")
        return student

    @staticmethod
    def update_student(db: Session, student_id: int, payload: StudentProfileUpdate):
        """Update: កែប្រែព័ត៌មានសិស្ស"""
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(student, key, value)

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def delete_student(db: Session, student_id: int):
        """Delete: លុបប្រវត្តិរូបសិស្សចេញពីប្រព័ន្ធ"""
        student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

        db.delete(student)
        db.commit()
        return {"message": f"Student profile with ID {student_id} has been deleted successfully."}

    @staticmethod
    def import_students_from_excel(db: Session, file: UploadFile):
        """Import students in bulk from an uploaded Excel file (.xlsx)"""
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Please upload an Excel file.")
        
        try:
            contents = file.file.read()
            df = pd.read_excel(io.BytesIO(contents))
            
            # ផ្ទៀងផ្ទាត់ Column ដែលចាំបាច់
            required_columns = ['user_id', 'student_id', 'full_name']
            for col in required_columns:
                if col not in df.columns:
                    raise HTTPException(status_code=400, detail=f"Missing required column in Excel: {col}")

            imported_count = 0
            for _, row in df.iterrows():
                user_id = int(row['user_id'])
                student_id = str(row['student_id'])
                
                # រំលងប្រសិនបើមាន Student ID រួចហើយ
                exists = db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first()
                if exists:
                    continue

                profile = StudentProfile(
                    user_id=user_id,
                    student_id=student_id,
                    full_name=str(row['full_name']),
                    gender=str(row.get('gender', '')) if pd.notna(row.get('gender')) else None,
                    department=str(row.get('department', '')) if pd.notna(row.get('department')) else None,
                    major=str(row.get('major', '')) if pd.notna(row.get('major')) else None,
                    academic_year=str(row.get('academic_year', '')) if pd.notna(row.get('academic_year')) else None,
                    class_name=str(row.get('class_name', '')) if pd.notna(row.get('class_name')) else None,
                    phone=str(row.get('phone', '')) if pd.notna(row.get('phone')) else None,
                    profile_completed=True
                )
                db.add(profile)
                imported_count += 1

            db.commit()
            return {"message": f"Successfully imported {imported_count} student profiles from Excel."}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error processing Excel file: {str(e)}")