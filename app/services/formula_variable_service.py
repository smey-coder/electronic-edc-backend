from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.formula import Formula, FormulaVariable


# =========================================
# Helpers
# =========================================

def get_formula_or_404(db: Session, formula_id: int):

    formula = (
        db.query(Formula)
        .filter(Formula.id == formula_id)
        .first()
    )

    if not formula:
        raise ValueError("Formula not found.")

    return formula


def get_variable_or_404(
    db: Session,
    formula_id: int,
    variable_id: int,
):

    variable = (
        db.query(FormulaVariable)
        .filter(
            FormulaVariable.id == variable_id,
            FormulaVariable.formula_id == formula_id,
        )
        .first()
    )

    if not variable:
        raise ValueError("Formula variable not found.")

    return variable


# =========================================
# GET ALL VARIABLES
# =========================================

def get_variables(
    db: Session,
    formula_id: int,
):

    get_formula_or_404(db, formula_id)

    return (
        db.query(FormulaVariable)
        .filter(FormulaVariable.formula_id == formula_id)
        .order_by(
            FormulaVariable.sort_order.asc(),
            FormulaVariable.id.asc(),
        )
        .all()
    )


# =========================================
# GET VARIABLE BY ID
# =========================================

def get_variable(
    db: Session,
    formula_id: int,
    variable_id: int,
):

    return get_variable_or_404(
        db,
        formula_id,
        variable_id,
    )


# =========================================
# CREATE VARIABLE
# =========================================

def create_variable(
    db: Session,
    formula_id: int,
    payload,
):

    get_formula_or_404(db, formula_id)

    variable = FormulaVariable(
        formula_id=formula_id,
        variable_name=payload.variable_name,
        display_name=payload.display_name,
        unit=payload.unit,
        default_value=payload.default_value,
        sort_order=payload.sort_order,
    )

    try:
        db.add(variable)
        db.commit()
        db.refresh(variable)

        return variable

    except IntegrityError:
        db.rollback()

        raise ValueError(
            f"Variable '{payload.variable_name}' already exists "
            "in this formula."
        )


# =========================================
# UPDATE VARIABLE
# =========================================

def update_variable(
    db: Session,
    formula_id: int,
    variable_id: int,
    payload,
):

    variable = get_variable_or_404(
        db,
        formula_id,
        variable_id,
    )

    data = payload.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(variable, key, value)

    try:
        db.commit()
        db.refresh(variable)

        return variable

    except IntegrityError:
        db.rollback()

        raise ValueError(
            "Variable name already exists in this formula."
        )


# =========================================
# DELETE VARIABLE
# =========================================

def delete_variable(
    db: Session,
    formula_id: int,
    variable_id: int,
):

    variable = get_variable_or_404(
        db,
        formula_id,
        variable_id,
    )

    db.delete(variable)
    db.commit()

    return True


# =========================================
# BULK REPLACE VARIABLES
# =========================================

def bulk_replace_variables(
    db: Session,
    formula_id: int,
    payload,
):

    formula = get_formula_or_404(db, formula_id)

    variables_data = [
        variable.model_dump()
        for variable in payload.variables
    ]

    names = [
        variable["variable_name"]
        for variable in variables_data
    ]

    if len(names) != len(set(names)):
        raise ValueError(
            "Duplicate variable names are not allowed."
        )

    try:
        # Remove previous variables
        formula.variables.clear()

        # Add new variables
        for variable in variables_data:

            formula.variables.append(
                FormulaVariable(**variable)
            )

        db.commit()
        db.refresh(formula)

        return (
            db.query(FormulaVariable)
            .filter(FormulaVariable.formula_id == formula_id)
            .order_by(
                FormulaVariable.sort_order.asc(),
                FormulaVariable.id.asc(),
            )
            .all()
        )

    except IntegrityError:
        db.rollback()

        raise ValueError(
            "Unable to replace formula variables."
        )