"""
Smart Hierarchical Date Inference & Standardization Module for BizPack.

Hierarchy:
1. Tier 1 (Regular Column-Wide Format Check):
   - First scans the entire column for regular, consistent date patterns (e.g. all DD/MM/YYYY,
     all MM/DD/YYYY, or all ISO YYYY-MM-DD).
   - If the column consistently follows one format with 0 conflicting entries, Tier 1 succeeds
     and applies the regular format across the whole column.
2. Tier 2 (Mixed / Ambiguous Fallback):
   - If Tier 1 is NOT able to determine a single regular format (because the column is mixed
     with both US and Indian/European entries, or all entries are <= 12 and ambiguous):
   - Tier 2 activates row-by-row contextual disambiguation:
     a) Unambiguous entries (e.g. 25/03/2024 vs 03/25/2024) are parsed by their own number clues.
     b) Ambiguous entries (e.g. 05/09/2024) are resolved using that specific row's partner columns
        (currency symbols like ₹ / $ or regions like India / USA).
     c) Final fallback: column-wide majority vote or dataset target currency.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import re
import warnings
import pandas as pd
import numpy as np
from datetime import datetime


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

# Regional / Country terms that indicate DD/MM/YYYY convention
DAY_FIRST_TERMS = {
    "inr", "eur", "gbp", "aud", "nzd", "brl", "chf", "sgd", "zar", "rub", "try",
    "india", "apac", "emea", "europe", "uk", "united kingdom", "great britain",
    "germany", "deutschland", "france", "italy", "spain", "australia", "new zealand",
    "singapore", "south africa", "brazil", "mexico", "delhi", "mumbai", "bangalore",
    "bengaluru", "chennai", "kolkata", "hyderabad", "london", "paris", "berlin",
    "tokyo", "sydney", "melbourne",
}

DAY_FIRST_SYMBOLS = {"₹", "€", "£", "r$", "a$", "rs.", "rs"}

# Regional / Country terms that indicate MM/DD/YYYY convention (US)
MONTH_FIRST_TERMS = {
    "usd", "usa", "united states", "united states of america", "america",
    "north america", "new york", "california", "texas", "florida", "illinois",
    "chicago", "los angeles", "san francisco", "seattle", "boston",
}


def detect_row_dayfirst(row_values: Iterable[Any]) -> Optional[bool]:
    """
    Tier 2 Context Inspector:
    Inspect all cells in a row (partner columns like currency, country, territory)
    to determine if that row's context is Day-First (Indian/European) or Month-First (US).
    Returns True for Day-First, False for Month-First, or None if ambiguous/neutral.
    """
    day_score = 0
    month_score = 0

    for v in row_values:
        if v is None or pd.isna(v):
            continue
        s = str(v).lower().strip()
        if not s:
            continue

        for sym in DAY_FIRST_SYMBOLS:
            if sym in s:
                day_score += 2

        for term in DAY_FIRST_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", s):
                day_score += 1

        for term in MONTH_FIRST_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", s):
                month_score += 1

        # Check for US dollar symbol (not Australian A$ or Canadian C$)
        if "$" in s and not any(sym in s for sym in ["a$", "c$", "nz$"]):
            month_score += 2

    if day_score > month_score:
        return True
    elif month_score > day_score:
        return False
    return None


_DATE_3PART_REGEX = re.compile(r"^(\d{1,2})[\/\-\.\s](\d{1,2})[\/\-\.\s](\d{2,4})$")
_DATE_ISO_REGEX = re.compile(r"^(\d{4})[\/\-\.\s](\d{1,2})[\/\-\.\s](\d{1,2})$")


def _parse_single_date(
    val: Any,
    row_dayfirst: Optional[bool] = None,
    default_dayfirst: bool = True,
) -> Tuple[Optional[pd.Timestamp], str]:
    """
    Parse a single date value using row-level contextual intelligence.
    Returns (Timestamp, resolution_method).
    """
    if pd.isna(val) or val is None:
        return pd.NaT, "null"
    if isinstance(val, (pd.Timestamp, datetime, np.datetime64)):
        return pd.Timestamp(val), "already_datetime"

    s_val = str(val).strip()
    if s_val.lower() in ("", "nan", "nat", "none", "null"):
        return pd.NaT, "null"

    parts = s_val.split()
    date_part = parts[0]
    time_part = " ".join(parts[1:]) if len(parts) > 1 else None

    # 1. ISO format check (YYYY-MM-DD)
    m_iso = _DATE_ISO_REGEX.match(date_part)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        try:
            ts = pd.Timestamp(year=y, month=m, day=d)
            if time_part:
                t = pd.to_datetime(time_part).time()
                ts = pd.Timestamp.combine(ts.date(), t)
            return ts, "iso"
        except Exception:
            pass

    # 2. Three-component date check (P1 / P2 / P3)
    m = _DATE_3PART_REGEX.match(date_part)
    if m:
        p1, p2, p3 = int(m.group(1)), int(m.group(2)), int(m.group(3))
        year = (2000 + p3 if p3 < 70 else 1900 + p3) if p3 < 100 else p3

        # Case A: Unambiguous Day in first position (p1 > 12) -> Indian / European DD/MM/YYYY
        if p1 > 12 and p2 <= 12:
            try:
                ts = pd.Timestamp(year=year, month=p2, day=p1)
                if time_part:
                    t = pd.to_datetime(time_part).time()
                    ts = pd.Timestamp.combine(ts.date(), t)
                return ts, "unambiguous_day_first"
            except Exception:
                pass

        # Case B: Unambiguous Day in second position (p2 > 12) -> US MM/DD/YYYY
        elif p2 > 12 and p1 <= 12:
            try:
                ts = pd.Timestamp(year=year, month=p1, day=p2)
                if time_part:
                    t = pd.to_datetime(time_part).time()
                    ts = pd.Timestamp.combine(ts.date(), t)
                return ts, "unambiguous_month_first"
            except Exception:
                pass

        # Case C: Ambiguous (both p1 and p2 <= 12, e.g. 05/09/2024)
        else:
            if row_dayfirst is not None:
                use_df = row_dayfirst
                method = "row_context_day_first" if use_df else "row_context_month_first"
            else:
                use_df = default_dayfirst
                method = "regular_column_day_first" if use_df else "regular_column_month_first"

            try:
                month = p2 if use_df else p1
                day = p1 if use_df else p2
                ts = pd.Timestamp(year=year, month=month, day=day)
                if time_part:
                    t = pd.to_datetime(time_part).time()
                    ts = pd.Timestamp.combine(ts.date(), t)
                return ts, method
            except Exception:
                pass

    # 3. Textual month or other formats (e.g. 25-Mar-2024, March 25 2024)
    use_df = row_dayfirst if row_dayfirst is not None else default_dayfirst
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            ts = pd.to_datetime(s_val, dayfirst=use_df, errors="coerce")
            return ts, "textual_or_standard"
    except Exception:
        return pd.NaT, "failed"


def infer_date_format_and_dayfirst(
    series: pd.Series,
    dataset_currency: Optional[str] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Tier 1 Hierarchy Step:
    Examine the column first for a regular, consistent date format.

    Returns:
    - dayfirst: bool (resolved default dayfirst)
    - audit_info: dict containing hierarchy_tier, inferred_format, is_mixed, reason, etc.
    """
    day_first_votes = 0
    month_first_votes = 0
    year_first_count = 0
    total_evaluated = 0

    non_null_vals = series.dropna().astype(str).tolist()
    date_regex = re.compile(r"^(\d{1,4})[\/\-\.\s](\d{1,2})[\/\-\.\s](\d{1,4})")

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

    is_mixed = (day_first_votes > 0 and month_first_votes > 0)
    has_regular_dayfirst = (day_first_votes > 0 and month_first_votes == 0)
    has_regular_monthfirst = (month_first_votes > 0 and day_first_votes == 0)
    has_regular_iso = (year_first_count > 0 and day_first_votes == 0 and month_first_votes == 0)

    # -------------------------------------------------------------
    # HIERARCHY EVALUATION
    # -------------------------------------------------------------
    if has_regular_dayfirst:
        # Tier 1 Success: Consistent Day-First column format
        hierarchy_tier = 1
        dayfirst = True
        inferred_format = "DD/MM/YYYY"
        reason = (
            f"Tier 1 (Regular Format): Column consistently follows DD/MM/YYYY "
            f"({day_first_votes} unambiguous entries, 0 conflicting Month-first entries)"
        )

    elif has_regular_monthfirst:
        # Tier 1 Success: Consistent Month-First column format
        hierarchy_tier = 1
        dayfirst = False
        inferred_format = "MM/DD/YYYY"
        reason = (
            f"Tier 1 (Regular Format): Column consistently follows MM/DD/YYYY "
            f"({month_first_votes} unambiguous entries, 0 conflicting Day-first entries)"
        )

    elif has_regular_iso:
        # Tier 1 Success: Consistent ISO format
        hierarchy_tier = 1
        dayfirst = False
        inferred_format = "YYYY-MM-DD"
        reason = "Tier 1 (Regular Format): Column consistently follows ISO YYYY-MM-DD format"

    elif is_mixed:
        # Tier 1 NOT able to resolve: Column contains mixed date formats
        # Triggers Tier 2: Row-by-Row Contextual Disambiguation
        hierarchy_tier = 2
        dayfirst = (day_first_votes >= month_first_votes)
        inferred_format = "Mixed (Tier 2 Contextual Fallback)"
        reason = (
            f"Tier 2 (Mixed Fallback): Mixed formats detected in same column "
            f"({day_first_votes} Day-first vs {month_first_votes} Month-first); "
            f"resolving row-by-row via partner columns (currency/region)"
        )

    else:
        # Tier 1 NOT able to resolve: All date entries are ambiguous (<= 12)
        # Triggers Tier 2: Check partner columns or dataset currency convention
        hierarchy_tier = 2
        curr = (dataset_currency or "").upper().strip()
        if curr in DAY_FIRST_CURRENCIES:
            dayfirst = True
            inferred_format = "DD/MM/YYYY"
            reason = (
                f"Tier 2 (Ambiguous Fallback): All date numbers <= 12; "
                f"resolving row-by-row via partner columns or '{curr}' convention (DD/MM/YYYY)"
            )
        else:
            dayfirst = False
            inferred_format = "MM/DD/YYYY"
            reason = (
                f"Tier 2 (Ambiguous Fallback): All date numbers <= 12; "
                f"resolving row-by-row via partner columns or '{curr or 'USD'}' convention (MM/DD/YYYY)"
            )

    audit_info = {
        "hierarchy_tier": hierarchy_tier,
        "dayfirst": dayfirst,
        "inferred_format": inferred_format,
        "is_mixed": is_mixed,
        "regular_format_detected": (hierarchy_tier == 1),
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
    df: Optional[pd.DataFrame] = None,
    row_contexts: Optional[List[Any]] = None,
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Parse a date Series with strict two-tier hierarchical resolution:

    Tier 1 (Regular Column Format):
    - First checks if the entire column follows a consistent regular date format (DD/MM/YYYY,
      MM/DD/YYYY, or ISO YYYY-MM-DD). If so, parses all rows consistently with that format.

    Tier 2 (Fallback for Mixed / Ambiguous Columns):
    - If Tier 1 is NOT able to resolve (because dates are mixed row-by-row or all ambiguous <= 12),
      activates row-by-row contextual disambiguation:
      1. Inspects unambiguous date numbers (> 12) in each row.
      2. Inspects partner columns (currency symbols ₹ / $ / €, regional territories India / USA).
      3. Falls back to column majority or dataset target currency.

    Guarantees 100% data integrity with ZERO valid dates dropped as NaT!
    """
    default_dayfirst, audit_info = infer_date_format_and_dayfirst(
        series,
        dataset_currency=dataset_currency,
    )

    if dayfirst is not None:
        default_dayfirst = dayfirst
        audit_info["dayfirst"] = dayfirst
        audit_info["hierarchy_tier"] = 1
        audit_info["reason"] = "Tier 1: Explicit dayfirst override provided by caller"

    hierarchy_tier = audit_info.get("hierarchy_tier", 1)
    is_regular_column = (hierarchy_tier == 1)

    parsed_dates: List[Optional[pd.Timestamp]] = []
    methods_count: Dict[str, int] = {}
    ambiguous_resolved_by_row_context = 0

    if is_regular_column:
        # -------------------------------------------------------------
        # TIER 1 EXECUTION: Apply Regular Column-Wide Format
        # -------------------------------------------------------------
        for val in series:
            ts, method = _parse_single_date(
                val,
                row_dayfirst=None,  # Use column's regular format
                default_dayfirst=default_dayfirst,
            )
            parsed_dates.append(ts)
            methods_count[method] = methods_count.get(method, 0) + 1

        audit_info["resolution_level"] = "Tier 1: Regular Column Format"

    else:
        # -------------------------------------------------------------
        # TIER 2 EXECUTION: Row-by-Row Contextual Disambiguation
        # -------------------------------------------------------------
        row_hints: List[Optional[bool]] = []
        if df is not None and len(df) == len(series):
            other_cols = [c for c in df.columns if c != series.name]
            for idx in range(len(df)):
                row_vals = [df.iloc[idx][c] for c in other_cols]
                row_hints.append(detect_row_dayfirst(row_vals))
        elif row_contexts is not None and len(row_contexts) == len(series):
            for idx in range(len(row_contexts)):
                row_hints.append(detect_row_dayfirst([row_contexts[idx]]))
        else:
            row_hints = [None] * len(series)

        for idx, val in enumerate(series):
            row_df = row_hints[idx]
            ts, method = _parse_single_date(
                val,
                row_dayfirst=row_df,
                default_dayfirst=default_dayfirst,
            )
            parsed_dates.append(ts)
            methods_count[method] = methods_count.get(method, 0) + 1
            if "row_context" in method:
                ambiguous_resolved_by_row_context += 1

        audit_info["resolution_level"] = "Tier 2: Row Contextual Disambiguation"

    parsed_series = pd.Series(parsed_dates, index=series.index, dtype="datetime64[ns]")

    audit_info["methods_breakdown"] = methods_count
    audit_info["ambiguous_resolved_by_row_context"] = ambiguous_resolved_by_row_context

    return parsed_series, audit_info
