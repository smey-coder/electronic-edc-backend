import ast
import math
import operator

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.formula import (
    Formula,
    FormulaCategory,
    FormulaVariable,
)


# =========================================
# Safe Formula Evaluator
# =========================================

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_calculate(expression: str, variables: dict) -> float:
    """
    Safely calculate arithmetic expressions.
    Does not use Python eval().
    """

    expression = expression.replace("^", "**")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ValueError("Invalid mathematical expression.")

    def evaluate(node):

        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)

            raise ValueError("Invalid constant.")

        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError(
                    f"Missing variable: {node.id}"
                )

            return float(variables[node.id])

        if isinstance(node, ast.BinOp):
            operation = BINARY_OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operator.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large.")

            result = operation(left, right)

            if not math.isfinite(result):
                raise ValueError("Calculation result is not finite.")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = UNARY_OPERATORS.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported unary operator.")

            return operation(evaluate(node.operand))

        raise ValueError("Unsupported expression.")

    try:
        result = evaluate(tree)
    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero.")
    except OverflowError:
        raise ValueError("Calculation result is too large.")

    if not math.isfinite(result):
        raise ValueError("Invalid calculation result.")

    return round(float(result), 6)


# =========================================
# Formula Category Services
# =========================================
def get_categories(db: Session):
    return (
        db.query(FormulaCategory)
        .order_by(FormulaCategory.name.asc())
        .all()
    )


def get_category(db: Session, category_id: int):
    return (
        db.query(FormulaCategory)
        .filter(FormulaCategory.id == category_id)
        .first()
    )


def create_category(db: Session, payload):
    category = FormulaCategory(
        name=payload.name,
        description=payload.description,
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except IntegrityError:
        db.rollback()
        raise ValueError("Category name already exists.")


def update_category(db: Session, category_id: int, payload):
    category = get_category(db, category_id)

    if not category:
        raise ValueError("Category not found.")

    data = payload.model_dump(exclude_unset=True)

    for key, value in data.items():
        setattr(category, key, value)

    try:
        db.commit()
        db.refresh(category)
        return category
    except IntegrityError:
        db.rollback()
        raise ValueError("Category name already exists.")


def delete_category(db: Session, category_id: int):
    category = get_category(db, category_id)

    if not category:
        raise ValueError("Category not found.")

    db.delete(category)
    db.commit()

    return True


# =========================================
# Formula Services
# =========================================
def get_formulas(db: Session, category_id=None, search=None):

    query = db.query(Formula).options(
        joinedload(Formula.category),
        joinedload(Formula.variables),
    )

    if category_id is not None:
        query = query.filter(
            Formula.category_id == category_id
        )

    if search:
        query = query.filter(
            Formula.title.ilike(f"%{search}%")
        )

    return query.order_by(Formula.id.desc()).all()


def get_formula(db: Session, formula_id: int):

    return (
        db.query(Formula)
        .options(
            joinedload(Formula.category),
            joinedload(Formula.variables),
        )
        .filter(Formula.id == formula_id)
        .first()
    )


def create_formula(db: Session, payload, current_user_id: int):

    if payload.category_id is not None:
        category = get_category(db, payload.category_id)

        if not category:
            raise ValueError("Category not found.")

    formula = Formula(
        category_id=payload.category_id,
        title=payload.title,
        expression=payload.expression,
        display_formula=payload.display_formula,  
        custom_logic=payload.custom_logic,
        result_unit=payload.result_unit,
        description=payload.description,
        created_by=current_user_id,
    )

    for variable in payload.variables:
        formula.variables.append(
            FormulaVariable(
                variable_name=variable.variable_name,
                display_name=variable.display_name,
                unit=variable.unit,
                default_value=variable.default_value,
                sort_order=variable.sort_order,
            )
        )

    try:
        db.add(formula)
        db.commit()
        db.refresh(formula)

        return get_formula(db, formula.id)

    except IntegrityError:
        db.rollback()
        raise ValueError(
            "Unable to create formula. Check category and variables."
        )


def update_formula(db: Session, formula_id: int, payload):
    formula = get_formula(db, formula_id)
    if not formula:
        raise ValueError("Formula not found.")

    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data and data["category_id"] is not None:
        if not get_category(db, data["category_id"]):
            raise ValueError("Category not found.")

    variables = data.pop("variables", None)

    for key, value in data.items():
        setattr(formula, key, value)

    if variables is not None:
        # លុប variables ចាស់ចេញពី database ដោយផ្ទាល់ ឬ clearing relationship
        db.query(FormulaVariable).filter(FormulaVariable.formula_id == formula_id).delete()
        
        for variable in variables:
            # ធានាថា variable_name ត្រូវបានបំប្លែងជាអក្សរតូច (lowercase) ជានិច្ច
            var_dict = dict(variable)
            if "variable_name" in var_dict:
                var_dict["variable_name"] = var_dict["variable_name"].strip().lower()
                
            new_var = FormulaVariable(formula_id=formula.id, **var_dict)
            db.add(new_var)

    try:
        db.commit()
        db.refresh(formula)
        return get_formula(db, formula.id)

    except IntegrityError as e:
        db.rollback()
        # បង្ហាញ Error message ពិតប្រាកដពី database ជំនួសឱ្យการจับ rix ទាំងអស់
        error_detail = str(e.orig) if hasattr(e, 'orig') else str(e)
        raise ValueError(
            f"Database Integrity Error: {error_detail}"
        )


def delete_formula(db: Session, formula_id: int):

    formula = get_formula(db, formula_id)

    if not formula:
        raise ValueError("Formula not found.")

    db.delete(formula)
    db.commit()

    return True
# =========================================
# Formula Calculation Service
# =========================================
def calculate_formula(
    db: Session,
    formula_id: int,
    input_variables: dict,
):

    formula = get_formula(db, formula_id)

    if not formula:
        raise ValueError("Formula not found.")

    required_variables = {
        variable.variable_name
        for variable in formula.variables
    }

    missing_variables = required_variables - set(input_variables.keys())

    if missing_variables:
        raise ValueError(
            "Missing variables: " + ", ".join(sorted(missing_variables))
        )

    calculation_inputs = {
        key: input_variables[key]
        for key in required_variables
    }

    # ត្រួតពិនិត្យ និងគណនាដោយផ្អែកលើ custom_logic ប្រសិនបើមាន
    if formula.custom_logic and formula.custom_logic.strip():
        try:
            # ឬប្រើវិធីសុវត្ថិភាពជាងនេះតាមការចង់បាន ឧទាហរណ៍ eval/exec ក្នុង scope កំណត់
            local_vars = {"values": calculation_inputs, "math": math}
            # Execute custom logic snippet (ឧ. return values['I'] * values['R'])
            result = eval(f"lambda values: ({formula.custom_logic.strip().replace('return ', '')})(values)", {"__builtins__": {}}, local_vars)(calculation_inputs)
            result = round(float(result), 6)
        except Exception as e:
            raise ValueError(f"Custom logic calculation error: {str(e)}")
    else:
        # ប្រើប្រាស់ safe_calculate តាមស្តង់ដារ AST ដើម
        result = safe_calculate(
            formula.expression,
            calculation_inputs,
        )

    return {
        "formula_id": formula.id,
        "formula_title": formula.title,
        "expression": formula.display_formula or formula.expression,  # បង្ហាញ display_formula ប្រសិនបើមាន
        "inputs": calculation_inputs,
        "result": result,
        "unit": formula.result_unit,
    }