from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# =========================================
# Formula Variable Schemas
# =========================================

class FormulaVariableBase(BaseModel):
    variable_name: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    )

    display_name: str = Field(
        min_length=1,
        max_length=100,
    )

    unit: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    default_value: Optional[Decimal] = None

    sort_order: int = 0


class FormulaVariableCreate(FormulaVariableBase):
    pass


class FormulaVariableResponse(FormulaVariableBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# =========================================
# Formula Category Schemas
# =========================================

class FormulaCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class FormulaCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None


class FormulaCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================
# Formula Schemas
# =========================================

class FormulaCreate(BaseModel):
    category_id: Optional[int] = None

    title: str = Field(min_length=1, max_length=150)

    expression: str = Field(
        min_length=1,
        max_length=255,
    )

    description: Optional[str] = None

    variables: list[FormulaVariableCreate] = Field(
        default_factory=list,
    )


class FormulaUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=150)
    expression: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None

    variables: Optional[list[FormulaVariableCreate]] = None


class FormulaResponse(BaseModel):
    id: int
    category_id: Optional[int]
    title: str
    expression: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    variables: list[FormulaVariableResponse] = Field(
        default_factory=list,
    )

    model_config = ConfigDict(from_attributes=True)


# =========================================
# Formula Calculation Schemas
# =========================================

class FormulaCalculateRequest(BaseModel):
    variables: dict[str, float]


class FormulaCalculateResponse(BaseModel):
    formula_id: int
    formula_title: str
    expression: str
    inputs: dict[str, float]
    result: float