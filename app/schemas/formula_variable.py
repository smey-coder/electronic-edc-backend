from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FormulaVariableBase(BaseModel):

    variable_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    )

    display_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    unit: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    default_value: Optional[Decimal] = None

    sort_order: int = Field(default=0, ge=0)

    @field_validator("variable_name", "display_name")
    @classmethod
    def strip_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value


class FormulaVariableCreate(FormulaVariableBase):
    pass


class FormulaVariableUpdate(BaseModel):

    variable_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    )

    display_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    unit: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    default_value: Optional[Decimal] = None

    sort_order: Optional[int] = Field(default=None, ge=0)

    @field_validator("variable_name", "display_name")
    @classmethod
    def strip_optional_text(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value


class FormulaVariableResponse(FormulaVariableBase):

    id: int
    formula_id: int

    model_config = ConfigDict(from_attributes=True)


class FormulaVariableBulkCreate(BaseModel):

    variables: list[FormulaVariableCreate] = Field(
        default_factory=list,
        max_length=100,
    )