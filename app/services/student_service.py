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
        name = (file.filename or "").lower()
        if not name.endswith((".xlsx", ".xls")):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid file format. Please upload an Excel file.")
        try:
            df = pd.read_excel(io.BytesIO(file.file.read()), dtype=str)
        except Exception as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Cannot read the Excel file: {exc}")

        df.columns = [str(c).strip() for c in df.columns]
        missing = [c for c in ("user_id", "student_id", "full_name") if c not in df.columns]
        if missing:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Missing required column(s): {', '.join(missing)}")

        def cell(row, key):
            value = row.get(key)
            return None if pd.isna(value) else (str(value).strip() or None)

        imported, skipped, errors = 0, 0, []
        for index, row in df.iterrows():
            line = index + 2  # row 1 is the header
            try:
                user_id = int(float(cell(row, "user_id")))
            except (TypeError, ValueError):
                errors.append(f"Row {line}: user_id must be a number.")
                continue
            student_id, full_name = cell(row, "student_id"), cell(row, "full_name")
            if not student_id or not full_name:
                errors.append(f"Row {line}: student_id and full_name are required.")
                continue
            if db.query(StudentProfile).filter(StudentProfile.student_id == student_id).first():
                skipped += 1
                continue
            if not db.query(User).filter(User.id == user_id).first():
                errors.append(f"Row {line}: user {user_id} does not exist.")
                continue
            if db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first():
                errors.append(f"Row {line}: user {user_id} already has a profile.")
                continue
            try:
                with db.begin_nested():  # one bad row does not stop the others
                    db.add(StudentProfile(
                        user_id=user_id, student_id=student_id, full_name=full_name,
                        gender=cell(row, "gender"), department=cell(row, "department"),
                        major=cell(row, "major"), academic_year=cell(row, "academic_year"),
                        class_name=cell(row, "class_name"), phone=cell(row, "phone"),
                        profile_completed=True,
                    ))
                    db.flush()
                imported += 1
            except IntegrityError:
                errors.append(f"Row {line}: conflicts with existing data.")

        db.commit()
        return {"message": f"Imported {imported} student profile(s).",
                "imported": imported, "skipped": skipped, "errors": errors}