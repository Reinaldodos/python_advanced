"""
Pydantic models for EU-SILC survey units.

EU-SILC file structure
----------------------
D (register)  household level  → DB030 household ID, DB040 NUTS region, DB090 weight
R (register)  person level     → RB030 person ID, links to household
H (data)      household level  → HB030 ID, HY020 net income, HX040 size
P (data)      person 16+       → PB030 ID, PY010G employment income
"""
from __future__ import annotations

import statistics
import warnings
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class HouseholdModel(BaseModel):
    """One EU-SILC household (H-file row)."""

    survey_year:       int   = Field(..., ge=2004, le=2030)
    country:           str   = Field(..., min_length=2, max_length=2)
    household_id:      int   = Field(..., gt=0)
    disposable_income: float = Field(..., description="HY020 net disposable income (€)")
    total_income:      float = Field(0.0,  description="HY010 gross total income (€)")
    household_size:    int   = Field(1,    ge=1, le=30,   description="HX040")
    weight:            float = Field(1.0,  gt=0,          description="DB090 design weight")
    nuts_region:       Optional[str] = Field(None,        description="DB040")

    @field_validator("country", mode="before")
    @classmethod
    def normalise_country(cls, v: str) -> str:
        return str(v).strip().upper()

    @field_validator("disposable_income", "total_income", mode="before")
    @classmethod
    def coerce_income(cls, v) -> float:
        if v is None or str(v).strip() in ("", "NA"):
            return 0.0
        return float(v)

    @field_validator("household_size", mode="before")
    @classmethod
    def coerce_size(cls, v) -> int:
        if v is None or str(v).strip() in ("", "NA"):
            return 1
        return max(1, int(float(v)))

    @model_validator(mode="after")
    def income_sanity(self) -> HouseholdModel:
        if self.total_income > 0 and self.disposable_income > self.total_income * 1.5:
            warnings.warn(
                f"HH {self.household_id}: disposable > 150% of gross. Check data."
            )
        return self

    @property
    def equivalised_income(self) -> float:
        """Simplified OECD equivalised income (full roster needed for precision)."""
        scale = 1.0 + 0.5 * (self.household_size - 1)
        return self.disposable_income / scale

    @property
    def tax_burden(self) -> float:
        return self.total_income - self.disposable_income


class PersonModel(BaseModel):
    """One EU-SILC person (P-file row, 16+)."""

    survey_year:       int   = Field(..., ge=2004, le=2030)
    country:           str   = Field(..., min_length=2, max_length=2)
    person_id:         int   = Field(..., gt=0)
    age:               int   = Field(..., ge=0, le=130)
    sex:               int   = Field(..., ge=1, le=2,  description="1=M 2=F")
    education:         Optional[int] = Field(None, description="PE040 ISCED level")
    labour_status:     Optional[int] = Field(None, description="PL031")
    employment_income: float = Field(0.0, description="PY010G gross (€)")
    pension_income:    float = Field(0.0, description="PY100G gross (€)")

    @field_validator("country", mode="before")
    @classmethod
    def normalise_country(cls, v: str) -> str:
        return str(v).strip().upper()

    @field_validator("employment_income", "pension_income", mode="before")
    @classmethod
    def coerce_income(cls, v) -> float:
        if v is None or str(v).strip() in ("", "NA"):
            return 0.0
        return float(v)

    @property
    def household_id(self) -> int:
        return self.person_id // 10

    @property
    def is_working_age(self) -> bool:
        return 15 <= self.age <= 64

    @property
    def sex_label(self) -> str:
        return {1: "Male", 2: "Female"}.get(self.sex, "Unknown")


class SurveyWave(BaseModel):
    """All households for one country × year pair."""

    country:    str
    year:       int
    households: list[HouseholdModel] = []

    @property
    def _positive_incomes(self) -> list[float]:
        return [hh.equivalised_income for hh in self.households
                if hh.equivalised_income > 0]

    @property
    def median_income(self) -> float:
        inc = self._positive_incomes
        return statistics.median(inc) if inc else 0.0

    @property
    def poverty_threshold(self) -> float:
        """EU AROP threshold: 60% of median equivalised income."""
        return 0.6 * self.median_income

    @property
    def arop_rate(self) -> float:
        """Share of households below the poverty threshold."""
        thresh = self.poverty_threshold
        if not self.households or thresh == 0:
            return 0.0
        n_poor = sum(1 for hh in self.households if hh.equivalised_income < thresh)
        return n_poor / len(self.households)

    def summary(self) -> dict:
        return {
            "country":            self.country,
            "year":               self.year,
            "n_households":       len(self.households),
            "median_income":      round(self.median_income, 2),
            "poverty_threshold":  round(self.poverty_threshold, 2),
            "arop_rate":          round(self.arop_rate, 4),
        }
