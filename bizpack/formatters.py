"""
Presentation and executive reporting formatters for BizKit.
Converts clean numeric data into boardroom-ready formatted strings.
"""

from typing import Dict, Optional, Union
import numpy as np
import pandas as pd


def format_currency(
    series: pd.Series,
    symbol: str = "$",
    decimals: int = 2,
) -> pd.Series:
    """
    Format a numeric Series as currency strings with thousands separators.
    Example: 1250000.5 -> '$1,250,000.50'
    """
    def _fmt(val):
        if pd.isna(val) or val is None:
            return ""
        try:
            num = float(val)
            if num < 0:
                return f"-{symbol}{abs(num):,.{decimals}f}"
            return f"{symbol}{num:,.{decimals}f}"
        except (ValueError, TypeError):
            return str(val)

    return series.map(_fmt)


def format_percent(
    series: pd.Series,
    decimals: int = 1,
    is_ratio: bool = True,
) -> pd.Series:
    """
    Format a numeric Series as percentage strings.
    Example: 0.1542 -> '15.4%' (if is_ratio=True)
             15.42  -> '15.4%' (if is_ratio=False)
    """
    def _fmt(val):
        if pd.isna(val) or val is None:
            return ""
        try:
            num = float(val)
            pct = num * 100.0 if is_ratio else num
            return f"{pct:.{decimals}f}%"
        except (ValueError, TypeError):
            return str(val)

    return series.map(_fmt)


def format_accounting(
    series: pd.Series,
    symbol: str = "$",
    decimals: int = 2,
    dash_for_zero: bool = True,
) -> pd.Series:
    """
    Format a numeric Series in standard corporate accounting format:
    - Negatives in parentheses: ($1,250.00)
    - Positives: $1,250.00
    - Zeros: - (if dash_for_zero=True)
    """
    def _fmt(val):
        if pd.isna(val) or val is None:
            return ""
        try:
            num = float(val)
            if dash_for_zero and abs(num) < 1e-9:
                return "—"
            if num < 0:
                return f"({symbol}{abs(num):,.{decimals}f})"
            return f"{symbol}{num:,.{decimals}f}"
        except (ValueError, TypeError):
            return str(val)

    return series.map(_fmt)


def format_for_display(
    df: pd.DataFrame,
    formats: Optional[Dict[str, str]] = None,
    currency_symbol: str = "$",
) -> pd.DataFrame:
    """
    Restore currency, percentage, and accounting formatting for presentation or export.
    Uses auto-detected metadata stored in df.attrs['_biz_formats'] from bk.clean(),
    or user-provided dictionary mapping {column: 'currency' | 'percentage' | 'accounting'}.

    Example:
    >>> clean_df = bk.clean(raw_df)
    >>> # do calculations on clean_df...
    >>> display_df = bk.format_for_display(clean_df)
    """
    df = df.copy()
    col_formats = dict(df.attrs.get("_biz_formats", {}))
    if formats:
        col_formats.update(formats)

    for col, fmt_type in col_formats.items():
        if col not in df.columns:
            continue

        fmt_lower = fmt_type.lower()
        if fmt_lower == "currency":
            df[col] = format_currency(df[col], symbol=currency_symbol)
        elif fmt_lower in ("percentage", "percent"):
            # Check if values are ratios <= 1.0 or already whole percentages
            numeric_nonnull = pd.to_numeric(df[col], errors="coerce").dropna()
            is_ratio = (numeric_nonnull.abs().max() <= 1.0) if len(numeric_nonnull) > 0 else True
            df[col] = format_percent(df[col], is_ratio=is_ratio)
        elif fmt_lower == "accounting":
            df[col] = format_accounting(df[col], symbol=currency_symbol)

    return df
