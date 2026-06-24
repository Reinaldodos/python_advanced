"""
SQLAlchemy ORM models and helpers for the SILC SQLite database.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, create_engine, text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    country_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    households: Mapped[List["Household"]] = relationship(back_populates="country_ref")


class Household(Base):
    __tablename__ = "households"

    household_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )
    country: Mapped[str] = mapped_column(
        String(2), ForeignKey("countries.country_code")
    )
    survey_year: Mapped[int] = mapped_column(Integer)
    disposable_income: Mapped[float] = mapped_column(Float, default=0.0)
    total_income: Mapped[float] = mapped_column(Float, default=0.0)
    household_size: Mapped[int] = mapped_column(Integer, default=1)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    equiv_income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nuts_region: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    country_ref: Mapped["Country"] = relationship(back_populates="households")


def get_engine(db_path: Path):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def create_schema(engine) -> None:
    Base.metadata.create_all(engine)
