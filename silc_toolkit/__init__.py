"""
silc_toolkit — EU-SILC Analysis Toolkit
Advanced Python for Official Statistics · ICON-Institute 2026
"""
from .models import HouseholdModel, PersonModel, SurveyWave
from .functional import timer, log_call, validate_output, retry
from .loaders import load_incomes, load_household_df, load_multi_year
from .indicators import arop_rate, gini_coefficient, poverty_threshold, s80s20_ratio

__version__ = "0.1.0"
__all__ = [
    # models
    "HouseholdModel", "PersonModel", "SurveyWave",
    # functional
    "timer", "log_call", "validate_output", "retry",
    # loaders
    "load_incomes", "load_household_df", "load_multi_year",
    # indicators
    "arop_rate", "gini_coefficient", "poverty_threshold", "s80s20_ratio",
]
