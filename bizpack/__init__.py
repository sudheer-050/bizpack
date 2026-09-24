"""
BizPack - The Business & Data Analyst Toolkit for Python.
Zero-friction spreadsheet cleaning + intuitive business formulas.
"""

__version__ = "0.1.0"

from bizpack.cleaner import (
    clean,
    clean_file,
    clean_headers,
    clean_strings,
    clean_types,
    strip_totals,
    drop_empty,
    read_csv,
    read_excel,
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
from bizpack.currency import (
    detect_currency,
    convert_amount,
    standardize_currency_series,
    standardize_currency_df,
    standardize_currency_df as standardize_currency,
    DEFAULT_RATES_TO_USD,
    SYMBOL_TO_CODE,
    CODE_TO_SYMBOL,
)
# Import accessor to register pd.DataFrame.biz
import bizpack.accessor

__all__ = [
    "clean",
    "clean_file",
    "clean_headers",
    "clean_strings",
    "clean_types",
    "strip_totals",
    "drop_empty",
    "read_csv",
    "read_excel",
    "xlookup",
    "growth",
    "pareto",
    "run_rate",
    "format_currency",
    "format_percent",
    "format_accounting",
    "format_for_display",
    "detect_currency",
    "convert_amount",
    "standardize_currency_series",
    "standardize_currency_df",
    "standardize_currency",
    "DEFAULT_RATES_TO_USD",
    "SYMBOL_TO_CODE",
    "CODE_TO_SYMBOL",
]

