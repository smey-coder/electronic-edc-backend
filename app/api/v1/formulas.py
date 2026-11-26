from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, require_calculator_access

from app.models.user import User
from app.schemas.formula import (
    FormulaCreate,
    FormulaUpdate,
    FormulaResponse,
    FormulaCategoryCreate,
    FormulaCategoryUpdate,
    FormulaCategoryResponse,
    FormulaCalculateRequest,
    FormulaCalculateResponse,
)
from app.services import formula_service

from app.core.dependencies import require_role_and_permission


router = APIRouter(
    prefix="/formulas",
    tags=["Formula Management"],
    dependencies=[Depends(require_calculator_access)],
)
# =========================================
# CATEGORY ENDPOINTS
# =========================================

@router.get("/categories",response_model=list[FormulaCategoryResponse],)
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher", "Student"], "formula.read"))
):
    return formula_service.get_categories(db)

@router.post("/categories",response_model=FormulaCategoryResponse,status_code=status.HTTP_201_CREATED,)
def create_category(
    payload: FormulaCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula.create"))
):
    try:
        return formula_service.create_category(db, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.put("/categories/{category_id}",response_model=FormulaCategoryResponse,)
def update_category(category_id: int,payload: FormulaCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula.update"))
):
    try:
        return formula_service.update_category(
            db,
            category_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.delete("/categories/{category_id}",status_code=status.HTTP_204_NO_CONTENT,)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula.delete"))
):
    
    try:
        formula_service.delete_category(db, category_id)
        return None
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


# =========================================
# FORMULA ENDPOINTS
# =========================================

@router.get("",response_model=list[FormulaResponse],)
def list_formulas(
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=150),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher", "Student"], "formula.read"))
):
    return formula_service.get_formulas(
        db,
        category_id=category_id,
        search=search,
    )


@router.get("/{formula_id}",response_model=FormulaResponse,)
def get_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher", "Student"], "formula.read"))
):
    formula = formula_service.get_formula(db, formula_id)

    if not formula:
        raise HTTPException(
            status_code=404,
            detail="Formula not found.",
        )

    return formula


@router.post("",response_model=FormulaResponse,status_code=status.HTTP_201_CREATED,
)
def create_formula(
    payload: FormulaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula.create"))
):

    try:
        return formula_service.create_formula(
            db,
            payload,
            current_user_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.put("/{formula_id}",response_model=FormulaResponse,)
def update_formula(
    formula_id: int,
    payload: FormulaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula.update"))
):
   

    try:
        return formula_service.update_formula(
            db,
            formula_id,
            payload,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.delete(
    "/{formula_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher"], "formula.delete"))
):

    try:
        formula_service.delete_formula(db, formula_id)
        return None
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


# =========================================
# CALCULATION ENDPOINT
# =========================================

@router.post(
    "/{formula_id}/calculate",
    response_model=FormulaCalculateResponse,
)
def calculate_formula(
    formula_id: int,
    payload: FormulaCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_and_permission(["Admin", "Teacher", "Student"], "formula.calculate"))
):
    try:
        return formula_service.calculate_formula(
            db,
            formula_id,
            payload.variables,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) 