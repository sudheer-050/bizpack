"""
Smart Date Inference & Standardization Module for BizPack.
Automatically examines other entries in a column and regional/currency context
to resolve ambiguous dates (DD-MM-YYYY vs MM-DD-YYYY) with 100% column-wide consistency.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import re
import warnings
import pandas as pd


# Currencies whose native geographic regions use DD/MM/YYYY as primary date convention
DAY_FIRST_CURRENCIES = {
    "INR",  # India: DD/MM/YYYY
    "EUR",  # Europe: DD/MM/YYYY or DD.MM.YYYY
    "GBP",  # United Kingdom: DD/MM/YYYY
    "AUD",  # Australia: DD/MM/YYYY
    "NZD",  # New Zealand: DD/MM/YYYY
    "BRL",  # Brazil: DD/MM/YYYY
    "MXN",  # Mexico: DD/MM/YYYY
    "CHF",  # Switzerland: DD.MM.YYYY
    "SGD",  # Singapore: DD/MM/YYYY
    "ZAR",  # South Africa: DD/MM/YYYY
    "RUB",  # Russia: DD.MM.YYYY
    "TRY",  # Turkey: DD.MM.YYYY
}


def infer_date_format_and_dayfirst(
    series: pd.Series,
    dataset_currency: Optional[str] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Examine non-null entries across an entire date column to determine whether
    the column format is DD/MM/YYYY (dayfirst=True) or MM/DD/YYYY (dayfirst=False).

    Logic:
    1. Scans all entries matching PART1 [sep] PART2 [sep] PART3.
    2. If PART1 > 12 and PART2 <= 12 (e.g. 25/03/2024), PART1 must be Day -> vote for dayfirst=True.
    3. If PART2 > 12 and PART1 <= 12 (e.g. 03/25/2024), PART2 must be Day -> vote for dayfirst=False.
    4. If column has unambiguous votes, the majority vote decides the format for all rows.
    5. If all rows are <= 12 (ambiguous), falls back to the dataset's currency convention:
       - INR, EUR, GBP -> DD/MM/YYYY (dayfirst=True)
       - USD -> MM/DD/YYYY (dayfirst=False)
    """
    day_first_votes = 0
    month_first_votes = 0
    year_first_count = 0
    total_evaluated = 0

    non_null_vals = series.dropna().astype(str).tolist()

    date_regex = re.compile(r"^(\d{1,4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,4})$")

    for val in non_null_vals:
        s = val.strip().split()[0]  # Strip time component if present
        m = date_regex.match(s)
        if not m:
            continue

        p1, p2, p3 = int(m.group(1)), int(m.group(2)), int(m.group(3))

        # Check ISO format: YYYY-MM-DD
        if p1 > 1000:
            year_first_count += 1
            total_evaluated += 1
            continue

        # Check year in 3rd position: DD/MM/YYYY or MM/DD/YYYY
        if p3 > 31 or len(m.group(3)) in (2, 4):
            total_evaluated += 1
            # If p1 > 12, p1 must be Day (e.g. 25/03/2024)
            if p1 > 12 and p2 <= 12:
                day_first_votes += 1
            # If p2 > 12, p2 must be Day (e.g. 03/25/2024)
            elif p2 > 12 and p1 <= 12:
                month_first_votes += 1

    # Decision logic
    if day_first_votes > month_first_votes:
        dayfirst = True
        inferred_format = "DD/MM/YYYY"
        reason = f"Deduced from {day_first_votes} unambiguous entries in column where day > 12 was in first position"
    elif month_first_votes > day_first_votes:
        dayfirst = False
        inferred_format = "MM/DD/YYYY"
        reason = f"Deduced from {month_first_votes} unambiguous entries in column where day > 12 was in second position"
    elif year_first_count > 0 and year_first_count >= (day_first_votes + month_first_votes):
        dayfirst = False
        inferred_format = "YYYY-MM-DD"
        reason = "ISO format (YYYY-MM-DD) detected"
    else:
        # Ambiguous entries only (all values <= 12): rely on currency / regional context
        curr = (dataset_currency or "").upper().strip()
        if curr in DAY_FIRST_CURRENCIES:
            dayfirst = True
            inferred_format = "DD/MM/YYYY"
            reason = f"All entries ambiguous; resolved using dataset currency '{curr}' regional convention (DD/MM/YYYY)"
        else:
            dayfirst = False
            inferred_format = "MM/DD/YYYY"
            reason = f"All entries ambiguous; resolved using dataset currency '{curr or 'USD'}' convention (MM/DD/YYYY)"

    audit_info = {
        "dayfirst": dayfirst,
        "inferred_format": inferred_format,
        "reason": reason,
        "day_first_votes": day_first_votes,
        "month_first_votes": month_first_votes,
        "total_evaluated": total_evaluated,
    }

    return dayfirst, audit_info


def parse_dates_consistently(
    series: pd.Series,
    dayfirst: Optional[bool] = None,
    dataset_currency: Optional[str] = None,
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Parse a date Series with 100% column-wide consistency.
    Ensures that ambiguous rows (like 05/09/2024) are not randomly flipped between
    May 9th and September 5th based on neighboring values.
    """
    if dayfirst is None:
        dayfirst, audit_info = infer_date_format_and_dayfirst(series, dataset_currency=dataset_currency)
    else:
        audit_info = {
            "dayfirst": dayfirst,
            "inferred_format": "DD/MM/YYYY" if dayfirst else "MM/DD/YYYY",
            "reason": "Explicitly specified by caller",
        }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        # Parse consistently with the resolved dayfirst setting
        parsed = pd.to_datetime(series, dayfirst=dayfirst, errors="coerce")

    return parsed, audit_info
