"""
BizPack - The Business & Data Analyst Toolkit for Python.
Zero-friction spreadsheet cleaning + intuitive business formulas.
"""

__version__ = "0.1.0"

from bizpack.cleaner import (
    clean,
    clean_headers,
    clean_strings,
    clean_types,
    strip_totals,
    drop_empty,
)
from bizpack.formulas import (
    xlookup,
    growth,
    pareto,
    run_rate,
)
from bizpack.formatters import (
    format_currency,
    format_percent,
    format_accounting,
    format_for_display,
)
# Import accessor to register pd.DataFrame.biz
import bizpack.accessor

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
