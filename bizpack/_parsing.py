"""
Shared low-level number/currency-token parsing helpers.

Extracted from cleaner.py/currency.py so those two modules can import this one
at the top level instead of reaching into each other with deferred, in-function
imports (which existed only to break a circular dependency).
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import numpy as np
import pandas as pd

# Comprehensive list of global currency symbols and ISO codes (sorted by length descending)
CURRENCY_SYMBOLS: List[str] = [
    # Multi-character codes & symbols
    "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL", "MXN",
    "SGD", "HKD", "NZD", "SEK", "NOK", "DKK", "ZAR", "PLN", "CZK", "HUF", "ILS",
    "US$", "CA$", "AU$", "NZ$", "C$", "A$", "R$", "RS.", "Rs.", "RS", "Rs", "kr", "zł", "Kč", "Ft",
    # Single-character symbols
    "$", "€", "£", "¥", "₹", "₩", "₺", "₽", "₴", "₫", "฿", "₱", "₪",
]

# Short alphabetic symbols that also occur as ordinary word fragments or abbreviations
# (e.g. "Ft." for "Fort", "Kroger" containing "Kr", "Rs" inside unrelated text).
# Only treated as a currency symbol when adjacent to a digit.
AMBIGUOUS_ALPHA_SYMBOLS: Tuple[str, ...] = ("kr", "zł", "Kč", "Ft", "RS.", "Rs.", "RS", "Rs")


def alpha_symbol_near_digit(symbol: str, s: str) -> bool:
    """Return True if `symbol` appears immediately adjacent (allowing one space/dot) to a digit in `s`."""
    pattern = rf"(?:\d[\s.]*{re.escape(symbol)}\b|\b{re.escape(symbol)}[\s.]*\d)"
    return re.search(pattern, s, re.IGNORECASE) is not None


def _normalize_number_string(s: str) -> str:
    """
    Normalize international numeric strings into standard Python float format (e.g. '1234.56'):
    - European formatting: '1.250,50' -> '1250.50', '1250,50' -> '1250.50'
    - US/UK formatting: '1,250.50' -> '1250.50', '1250.50' -> '1250.50'
    - Swiss apostrophe separator: "1'250.50" -> '1250.50'
    - Space thousands separator: '1 250,50' or '1 250.50' -> '1250.50'
    - Multiple European dots: '1.000.000' -> '1000000'
    """
    # 1. Remove Swiss apostrophe thousands separator: e.g. 1'250.50 -> 1250.50
    s = s.replace("'", "")

    # 2. Remove spaces between digits: e.g. "1 250,50" -> "1250,50"
    s = re.sub(r"(?<=\d)\s+(?=\d)", "", s)

    has_comma = "," in s
    has_dot = "." in s

    if has_comma and has_dot:
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_comma > last_dot:
            # European style: 1.250,50 or 1.250.000,50 -> dot is thousand, comma is decimal
            s = s.replace(".", "").replace(",", ".")
        else:
            # US/UK style: 1,250.50 or 1,250,000.50 -> comma is thousand, dot is decimal
            s = s.replace(",", "")
    elif has_comma and not has_dot:
        # Only comma exists: e.g. "1250,50", "45,99", or "1,250"
        # If comma is followed by 1 or 2 digits at the end: European decimal!
        if re.search(r",\d{1,2}$", s):
            s = s.replace(",", ".")
        else:
            # Standard thousands separator: e.g. 1,000
            s = s.replace(",", "")
    elif has_dot and not has_comma:
        # Only dot exists: e.g. "1250.50", "1.000.000"
        if s.count(".") > 1:
            # Multiple dots e.g. 1.000.000 -> European thousands separator
            s = s.replace(".", "")

    return s


def parse_business_number(val: Any, percent_as_ratio: bool = True) -> Tuple[Optional[float], Optional[str]]:
    """
    Attempt to parse a messy business string into a float.
    Handles:
    - Normal numbers: '1250.50', '1,250'
    - European numbers: '1.250,50', '1250,50', '1 250,50 €'
    - Global Currencies: '$', '€', '£', '¥', 'CHF', 'R$', 'kr', 'EUR', 'USD', etc.
    - Accounting negatives: '(1,234.50)', '($1,234.50)', '(1.250,50 €)'
    - Negatives: '-$50.00', '-50.00', '-€ 1.250,50', '50.00-'
    - Percentages: '15.4%', '(2.5%)'
    """
    if pd.isna(val) or val is None:
        return np.nan, None

    s = str(val).strip()
    if not s:
        return np.nan, None

    detected_type = "number"
    is_negative = False

    # Check accounting parentheses: e.g. (1,234), ($1,234), (1.250,50 €)
    if "(" in s and ")" in s:
        left_paren = s.find("(")
        right_paren = s.rfind(")")
        if left_paren < right_paren:
            outside = (s[:left_paren] + s[right_paren + 1:]).strip()
            # If outside has no digits, it's an accounting negative number
            if not any(ch.isdigit() for ch in outside):
                is_negative = True
                detected_type = "accounting"
                s = s[:left_paren] + s[left_paren + 1:right_paren] + s[right_paren + 1:]
                s = s.strip()

    # Check percentage
    if s.endswith("%"):
        detected_type = "percentage"
        s = s[:-1].strip()

    # Check for currency symbols anywhere (prefix, suffix, or mid-string)
    for sym in CURRENCY_SYMBOLS:
        if sym not in s:
            continue
        if sym in AMBIGUOUS_ALPHA_SYMBOLS and not alpha_symbol_near_digit(sym, s):
            # e.g. "Ft" in "Ft. Worth" or "kr" in "Kroger" -- not actually a currency symbol here.
            continue
        detected_type = "currency"
        s = s.replace(sym, "")

    # Check for negative/positive signs
    s = s.strip()
    if s.startswith("-"):
        is_negative = True
        s = s[1:].strip()
    elif s.endswith("-"):
        is_negative = True
        s = s[:-1].strip()
    elif s.startswith("+"):
        s = s[1:].strip()

    # Normalize international number formatting (European commas/periods, Swiss apostrophes, spaces)
    s = _normalize_number_string(s).strip()

    try:
        num = float(s)
        if is_negative:
            num = -num
        if detected_type == "percentage" and percent_as_ratio:
            num = num / 100.0
        return num, detected_type
    except (ValueError, TypeError):
        return None, None
