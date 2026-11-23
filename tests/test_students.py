from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.student import StudentProfileCreate
from app.services.student_service import StudentService


def test_student_create_normalizes_gender():
    payload = StudentProfileCreate(
        user_id=1,
        student_id="ST-001",
        full_name="Test Student",
        gender="female",
    )

    assert payload.gender == "Female"


def test_student_create_rejects_gender_outside_database_constraint():
    with pytest.raises(ValidationError):
        StudentProfileCreate(
            user_id=1,
            student_id="ST-001",
            full_name="Test Student",
            gender="unknown",
        )


def test_student_create_reports_existing_user_profile():
    user_query = Mock()
    user_query.filter.return_value.first.return_value = object()
    student_id_query = Mock()
    student_id_query.filter.return_value.first.return_value = None
    profile_query = Mock()
    profile_query.filter.return_value.first.return_value = object()
    db = Mock()
    db.query.side_effect = [user_query, student_id_query, profile_query]
    payload = StudentProfileCreate(
        user_id=1,
        student_id="ST-001",
        full_name="Test Student",
    )

    with pytest.raises(HTTPException) as exc_info:
        StudentService.create_profile(db, payload)

    assert exc_info.value.status_code == 409
    db.add.assert_not_called()
    db.commit.assert_not_called()