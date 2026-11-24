from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user

from app.models.user import User
from app.schemas.formula_variable import (
    FormulaVariableCreate,
    FormulaVariableUpdate,
    FormulaVariableResponse,
    FormulaVariableBulkCreate,
)

from app.services import formula_variable_service
# from app.api.v1.formulas import ensure_manager
from app.core.dependencies import require_role_and_permission


router = APIRouter(
    prefix="/formulas/{formula_id}/variables",
    tags=["Formula Variables"],
)


# =========================================
# GET ALL VARIABLES
# =========================================

@router.get(
    "",
    response_model=list[FormulaVariableResponse],
)
def list_variables(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula_variable.read"))
):
    try:
        return formula_variable_service.get_variables(
            db,
            formula_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# =========================================
# GET VARIABLE BY ID
# =========================================

@router.get(
    "/{variable_id}",
    response_model=FormulaVariableResponse,
)
def get_variable(
    formula_id: int,
    variable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula_variable.read"))
):

    try:
        return formula_variable_service.get_variable(
            db,
            formula_id,
            variable_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# =========================================
# CREATE VARIABLE
# =========================================

@router.post(
    "",
    response_model=FormulaVariableResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_variable(
    formula_id: int,
    payload: FormulaVariableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula_variable.create"))
):

    try:
        return formula_variable_service.create_variable(
            db,
            formula_id,
            payload,
        )

    except ValueError as error:
        message = str(error)

        raise HTTPException(
            status_code=404 if message == "Formula not found." else 400,
            detail=message,
        )


# =========================================
# UPDATE VARIABLE
# =========================================

@router.put(
    "/{variable_id}",
    response_model=FormulaVariableResponse,
)
def update_variable(
    formula_id: int,
    variable_id: int,
    payload: FormulaVariableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula_variable.update"))
):

    try:
        return formula_variable_service.update_variable(
            db,
            formula_id,
            variable_id,
            payload,
        )

    except ValueError as error:
        message = str(error)

        raise HTTPException(
            status_code=404 if "not found" in message.lower() else 400,
            detail=message,
        )


# =========================================
# DELETE VARIABLE
# =========================================

@router.delete(
    "/{variable_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_variable(
    formula_id: int,
    variable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula_variable.delete"))
):


    try:
        formula_variable_service.delete_variable(
            db,
            formula_id,
            variable_id,
        )

        return None

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# =========================================
# BULK REPLACE VARIABLES
# =========================================

@router.put(
    "/bulk",
    response_model=list[FormulaVariableResponse],
)
def replace_variables(
    formula_id: int,
    payload: FormulaVariableBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula_variable.replace"))
):


    try:
        return formula_variable_service.bulk_replace_variables(
            db,
            formula_id,
            payload,
        )

    except ValueError as error:
        message = str(error)

        raise HTTPException(
            status_code=404 if message == "Formula not found." else 400,
            detail=message,
        )