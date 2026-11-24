from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    ForeignKey,
    Numeric,
    TIMESTAMP,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class FormulaCategory(Base):
    __tablename__ = "formula_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    formulas = relationship(
        "Formula",
        back_populates="category",
    )


class Formula(Base):
    __tablename__ = "formulas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    category_id = Column(
        Integer,
        ForeignKey(
            "formula_categories.id",
            ondelete="SET NULL",
            onupdate="CASCADE",
        ),
        nullable=True,
    )

    title = Column(String(150), nullable=False)
    expression = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Must match users.id = BIGINT
    created_by = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    category = relationship(
        "FormulaCategory",
        back_populates="formulas",
    )

    variables = relationship(
        "FormulaVariable",
        back_populates="formula",
        cascade="all, delete-orphan",
        order_by="FormulaVariable.sort_order",
    )

    __table_args__ = (
        Index("idx_category_id", "category_id"),
        Index("idx_created_by", "created_by"),
    )


class FormulaVariable(Base):
    __tablename__ = "formula_variables"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    formula_id = Column(
        Integer,
        ForeignKey(
            "formulas.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    variable_name = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=True)
    default_value = Column(Numeric(15, 6), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    formula = relationship(
        "Formula",
        back_populates="variables",
    )

    __table_args__ = (
        UniqueConstraint(
            "formula_id",
            "variable_name",
            name="uq_formula_variable",
        ),
        Index("idx_formula_id", "formula_id"),
    )