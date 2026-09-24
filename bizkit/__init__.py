"""
BizKit - The Business & Data Analyst Toolkit for Python.
Zero-friction spreadsheet cleaning + intuitive business formulas.
"""

__version__ = "0.1.0"

from bizkit.cleaner import (
    clean,
    clean_headers,
    clean_strings,
    clean_types,
    strip_totals,
    drop_empty,
)
from bizkit.formulas import (
    xlookup,
    growth,
    pareto,
    run_rate,
)
from bizkit.formatters import (
    format_currency,
    format_percent,
    format_accounting,
    format_for_display,
)
# Import accessor to register pd.DataFrame.biz
import bizkit.accessor

__all__ = [
    "clean",
    "clean_headers",
    "clean_strings",
    "clean_types",
    "strip_totals",
    "drop_empty",
    "xlookup",
    "growth",
    "pareto",
    "run_rate",
    "format_currency",
    "format_percent",
    "format_accounting",
    "format_for_display",
]
