"""
Core data cleaning module for BizKit.
Zero-friction spreadsheet and business data hygiene.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
import re
import unicodedata
import warnings
import numpy as np
import pandas as pd

# Default placeholder strings commonly found in business spreadsheets representing null/missing data
DEFAULT_NULL_STRINGS: Set[str] = {
    "",
    "-",
    "—",
    "–",
    "n/a",
    "na",
    "null",
    "none",
    "nil",
    "#n/a",
    "#value!",
    "#ref!",
    "#num!",
    "#div/0!",
    ".",
    "nan",
    "?",
}

# Comprehensive list of global currency symbols and ISO codes (sorted by length descending)
CURRENCY_SYMBOLS: List[str] = [
    # Multi-character codes & symbols
    "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL", "MXN",
    "SGD", "HKD", "NZD", "SEK", "NOK", "DKK", "ZAR", "PLN", "CZK", "HUF", "ILS",
    "US$", "CA$", "AU$", "NZ$", "C$", "A$", "R$", "RS.", "Rs.", "RS", "Rs", "kr", "zł", "Kč", "Ft",
    # Single-character symbols
    "$", "€", "£", "¥", "₹", "₩", "₺", "₽", "₴", "₫", "฿", "₱", "₪",
]

# Keywords indicating summary/total rows at the bottom of a sheet
TOTAL_ROW_KEYWORDS: List[str] = [
    "total",
    "grand total",
    "subtotal",
    "average",
    "avg",
    "summary",
    "totals",
]


def clean_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize DataFrame column names to clean, snake_case identifiers.
    - Strips whitespace
    - Lowercases all characters
    - Replaces spaces, slashes, dashes, and periods with underscores
    - Removes punctuation and special characters
    - Deduplicates identical column names (e.g. 'sales', 'sales_1')
    """
    df = df.copy()
    new_cols: List[str] = []
    seen: Dict[str, int] = {}

    for idx, col in enumerate(df.columns):
        col_str = str(col)
        # Normalize unicode
        normalized = unicodedata.normalize("NFKD", col_str).encode("ascii", "ignore").decode("utf-8")
        # Strip and lower
        cleaned = normalized.strip().lower()
        # Replace spaces, dashes, slashes, and periods with underscores
        cleaned = re.sub(r"[\s\-\/\.]+", "_", cleaned)
        # Remove special characters
        cleaned = re.sub(r"[^a-z0-9_]", "", cleaned)
        # Collapse multiple underscores
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")

        if not cleaned:
            cleaned = f"col_{idx}"

        # Handle duplicates
        if cleaned in seen:
            seen[cleaned] += 1
            new_col = f"{cleaned}_{seen[cleaned]}"
        else:
            seen[cleaned] = 0
            new_col = cleaned

        new_cols.append(new_col)

    df.columns = new_cols
    return df


def drop_empty(df: pd.DataFrame, drop_rows: bool = True, drop_cols: bool = True) -> pd.DataFrame:
    """
    Drop completely blank rows and/or columns (all NaN).
    """
    df = df.copy()
    if drop_rows:
        df = df.dropna(how="all")
    if drop_cols:
        df = df.dropna(axis=1, how="all")
    return df.reset_index(drop=True)


def strip_totals(
    df: pd.DataFrame,
    keywords: Optional[List[str]] = None,
    max_rows: int = 3,
) -> pd.DataFrame:
    """
    Detect and strip summary/total/subtotal rows commonly found at the bottom of spreadsheets.
    Stores any removed rows in df.attrs['totals'].
    """
    df = df.copy()
    if len(df) == 0:
        return df

    target_keywords = [k.lower() for k in (keywords or TOTAL_ROW_KEYWORDS)]
    rows_to_drop: List[int] = []

    # Check the last max_rows rows
    tail_indices = df.index[-max_rows:].tolist()
    for idx in reversed(tail_indices):
        row_vals = df.loc[idx].astype(str).str.lower().str.strip()
        # Check first column or any cell in the row for a total keyword
        is_total = False
        for val in row_vals:
            # Check if cell begins with or matches total keywords
            val_clean = re.sub(r"[:\-\*]", "", val).strip()
            if val_clean in target_keywords:
                is_total = True
                break

        if is_total:
            rows_to_drop.append(idx)
        else:
            # Once we hit a non-total row from the bottom, stop
            break

    if rows_to_drop:
        totals_records = df.loc[rows_to_drop].to_dict(orient="records")
        df = df.drop(index=rows_to_drop).reset_index(drop=True)
        if "totals" not in df.attrs:
            df.attrs["totals"] = totals_records
        else:
            df.attrs["totals"].extend(totals_records)

    return df


def clean_strings(
    df: pd.DataFrame,
    null_values: Optional[Set[str]] = None,
) -> pd.DataFrame:
    """
    Clean string columns:
    - Strips leading/trailing whitespace and hidden non-breaking spaces
    - Converts common business null placeholders ('-', 'N/A', '#VALUE!', 'None') to np.nan
    """
    df = df.copy()
    targets = {s.lower() for s in (null_values or DEFAULT_NULL_STRINGS)}

    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            # Clean string values
            def _clean_str(val):
                if val is None or pd.isna(val):
                    return np.nan
                if not isinstance(val, str):
                    val = str(val)
                # Strip non-breaking spaces and regular spaces
                s = val.replace("\xa0", " ").replace("\u200b", "").strip()
                if s.lower() in targets:
                    return np.nan
                return s

            df[col] = df[col].map(_clean_str)

    return df


def _is_id_column(col_name: str, series: pd.Series) -> bool:
    """
    Check if a column is likely an Identifier (e.g. ZIP code, Account Number, Phone, SSN)
    that should preserve leading zeros and avoid numeric casting.
    """
    name_lower = col_name.lower()
    id_suffixes = ("_id", "_code", "_num", "_no", "id", "zip", "zipcode", "ssn", "ein", "phone", "account")
    for suffix in id_suffixes:
        if name_lower == suffix or name_lower.endswith(suffix):
            return True

    # Check for leading zeros in non-null strings
    non_nulls = series.dropna().astype(str).tolist()
    if not non_nulls:
        return False

    leading_zero_count = sum(1 for val in non_nulls if len(val) > 1 and val.startswith("0") and val.isdigit())
    if leading_zero_count / len(non_nulls) >= 0.2:
        return True

    return False


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


def _parse_business_number(val: Any, percent_as_ratio: bool = True) -> Tuple[Optional[float], Optional[str]]:
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
        if sym in s:
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


def clean_types(
    df: pd.DataFrame,
    percent_as_ratio: bool = True,
    threshold: float = 0.85,
    date_threshold: float = 0.85,
    target_currency: Optional[str] = None,
    rates: Optional[Dict[str, float]] = None,
    prompt_currency: bool = True,
    keep_currency_col: bool = False,
    dayfirst: Optional[bool] = None,
) -> pd.DataFrame:
    """
    Auto-detect and convert dirty business columns to their proper dtypes:
    - Currency strings ('$1,250.00', '€500', '₹9,000') -> float64
      If multiple currencies are present, converts all amounts into target_currency
      (or prompts user interactively) to prevent math/financial errors.
    - Accounting negatives ('(450.00)', '($1,200)') -> float64 (negative)
    - Percentages ('15.4%', '(2.1%)') -> float64 (0.154 or 15.4)
    - Dates ('2024-01-15', '01/15/2024') -> datetime64[ns]
    - Booleans ('Y/N', 'yes/no', 'true/false') -> boolean
    - Protects ID and Zip code columns with leading zeros intact.

    Stores original formatting metadata in df.attrs['_biz_formats'] for later presentation.
    """
    df = df.copy()
    formats_meta: Dict[str, str] = {}
    active_target_currency = target_currency

    for col in df.columns:
        # Only inspect object or string columns
        if not (df[col].dtype == object or pd.api.types.is_string_dtype(df[col])):
            continue

        # Skip protected ID columns
        if _is_id_column(col, df[col]):
            continue

        non_null_series = df[col].dropna()
        if len(non_null_series) == 0:
            continue

        # Sample values for fast heuristic evaluation
        sample = non_null_series.sample(min(len(non_null_series), 200), random_state=42)

        # 1. Test for Business Numeric (Currency, Accounting, Percent, Number)
        numeric_count = 0
        type_votes: Dict[str, int] = {}
        for val in sample:
            num, d_type = _parse_business_number(val, percent_as_ratio=percent_as_ratio)
            if num is not None:
                numeric_count += 1
                type_votes[d_type] = type_votes.get(d_type, 0) + 1

        match_ratio = numeric_count / len(sample)
        if match_ratio >= threshold:
            dominant_type = max(type_votes.items(), key=lambda x: x[1])[0] if type_votes else "number"
            formats_meta[col] = dominant_type

            # Check if this column represents currency data
            from bizpack.currency import (
                standardize_currency_series,
                detect_currency,
                detect_header_currency,
            )
            has_currency = (
                (dominant_type == "currency")
                or (type_votes.get("currency", 0) > 0)
                or any(detect_currency(v) is not None for v in sample.head(25))
                or (detect_header_currency(str(col)) is not None)
            )

            if has_currency:
                converted_series, orig_curr_series, audit = standardize_currency_series(
                    df[col],
                    target_currency=active_target_currency,
                    rates=rates,
                    col_name=str(col),
                    prompt_if_interactive=prompt_currency,
                )
                df[col] = converted_series
                if "currency_conversions" not in df.attrs:
                    df.attrs["currency_conversions"] = {}
                df.attrs["currency_conversions"][col] = audit

                # Remember user's choice for subsequent currency columns if multiple currencies were resolved
                if len(audit.get("detected_currencies", [])) > 1 and "target_currency" in audit:
                    active_target_currency = audit["target_currency"]

                if keep_currency_col:
                    df[f"{col}_original_currency"] = orig_curr_series
                continue

            # Standard numeric column (e.g. quantity, percentages, clean floats)
            def _coerce(val):
                num, _ = _parse_business_number(val, percent_as_ratio=percent_as_ratio)
                return num if num is not None else np.nan

            df[col] = df[col].map(_coerce).astype(float)
            continue

        # 2. Test for Boolean Columns (e.g. Y/N, Yes/No, True/False)
        lower_vals = sample.astype(str).str.lower().str.strip()
        bool_map = {
            "y": True, "yes": True, "true": True, "t": True,
            "n": False, "no": False, "false": False, "f": False,
        }
        unique_lower = set(lower_vals.unique())
        if unique_lower.issubset(bool_map.keys()) and len(unique_lower) > 0:
            df[col] = df[col].astype(str).str.lower().str.strip().map(bool_map).astype("boolean")
            formats_meta[col] = "boolean"
            continue

        # 3. Test for Datetime (with column-wide format deduction from other entries)
        try:
            from bizpack.dates import parse_dates_consistently
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                test_parsed, _ = parse_dates_consistently(
                    sample,
                    dayfirst=dayfirst,
                    dataset_currency=active_target_currency,
                )
                date_ratio = test_parsed.notna().sum() / len(sample)
                if date_ratio >= date_threshold:
                    parsed_series, date_audit = parse_dates_consistently(
                        df[col],
                        dayfirst=dayfirst,
                        dataset_currency=active_target_currency,
                    )
                    df[col] = parsed_series
                    formats_meta[col] = "datetime"
                    if "date_formats" not in df.attrs:
                        df.attrs["date_formats"] = {}
                    df.attrs["date_formats"][col] = date_audit
                    continue
        except Exception:
            pass

    # Save format metadata in df.attrs
    if "_biz_formats" not in df.attrs:
        df.attrs["_biz_formats"] = {}
    df.attrs["_biz_formats"].update(formats_meta)

    return df


def clean(
    df: pd.DataFrame,
    headers: bool = True,
    strings: bool = True,
    totals: bool = True,
    empty: bool = True,
    types: bool = True,
    percent_as_ratio: bool = True,
    target_currency: Optional[str] = None,
    rates: Optional[Dict[str, float]] = None,
    prompt_currency: bool = True,
    keep_currency_col: bool = False,
    dayfirst: Optional[bool] = None,
) -> pd.DataFrame:
    """
    The master all-in-one cleaning function.
    Takes a messy DataFrame and produces a clean, analysis-ready DataFrame in one line.

    Steps performed:
    1. Standardizes headers (lowercase, snake_case, no special chars)
    2. Drops completely blank rows and columns
    3. Strips trailing 'Grand Total' summary rows (saves them to df.attrs['totals'])
    4. Cleans strings (strips whitespace, converts '-', 'N/A' to true np.nan)
    5. Auto-coerces types (currencies, accounting negatives, percentages, dates, booleans)
       while preserving ID and ZIP codes with leading zeros.
    6. Standardizes mixed currencies (e.g. USD, EUR, INR) into target_currency so financial
       calculations and aggregations are mathematically accurate.
    7. Resolves date formats (DD-MM-YYYY vs MM-DD-YYYY) by checking other entries in the column
       and regional/currency context.
    """
    df = df.copy()

    if headers:
        df = clean_headers(df)
    if empty:
        df = drop_empty(df)
    if totals:
        df = strip_totals(df)
    if strings:
        df = clean_strings(df)
    if types:
        df = clean_types(
            df,
            percent_as_ratio=percent_as_ratio,
            target_currency=target_currency,
            rates=rates,
            prompt_currency=prompt_currency,
            keep_currency_col=keep_currency_col,
            dayfirst=dayfirst,
        )
    return df


def read_csv(filepath_or_buffer: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Read a CSV file safely and automatically clean it with BizPack.
    Preserves leading zeros in IDs and ZIP codes by reading strings before type coercion.
    Supports currency standardization via target_currency='USD' or 'INR'.
    Automatically deduces date format (DD/MM/YYYY vs MM/DD/YYYY) from column entries and currency.
    """
    clean_kwargs = {
        "headers": kwargs.pop("headers", True),
        "strings": kwargs.pop("strings", True),
        "totals": kwargs.pop("totals", True),
        "empty": kwargs.pop("empty", True),
        "types": kwargs.pop("types", True),
        "percent_as_ratio": kwargs.pop("percent_as_ratio", True),
        "target_currency": kwargs.pop("target_currency", None),
        "rates": kwargs.pop("rates", None),
        "prompt_currency": kwargs.pop("prompt_currency", True),
        "keep_currency_col": kwargs.pop("keep_currency_col", False),
        "dayfirst": kwargs.pop("dayfirst", None),
    }
    if "dtype" not in kwargs:
        kwargs["dtype"] = str

    df = pd.read_csv(filepath_or_buffer, **kwargs)
    return clean(df, **clean_kwargs)


def read_excel(filepath_or_buffer: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Read an Excel file safely and automatically clean it with BizPack.
    Supports currency standardization via target_currency='USD' or 'INR'.
    Automatically deduces date format (DD/MM/YYYY vs MM/DD/YYYY) from column entries and currency.
    """
    clean_kwargs = {
        "headers": kwargs.pop("headers", True),
        "strings": kwargs.pop("strings", True),
        "totals": kwargs.pop("totals", True),
        "empty": kwargs.pop("empty", True),
        "types": kwargs.pop("types", True),
        "percent_as_ratio": kwargs.pop("percent_as_ratio", True),
        "target_currency": kwargs.pop("target_currency", None),
        "rates": kwargs.pop("rates", None),
        "prompt_currency": kwargs.pop("prompt_currency", True),
        "keep_currency_col": kwargs.pop("keep_currency_col", False),
        "dayfirst": kwargs.pop("dayfirst", None),
    }
    df = pd.read_excel(filepath_or_buffer, **kwargs)
    return clean(df, **clean_kwargs)


def clean_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    target_currency: Optional[str] = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Clean an entire spreadsheet file in ONE line.
    Automatically detects CSV vs Excel, standardizes mixed currencies by prompting
    in the output area, and saves to a brand new file without touching the original.
    
    Example:
    >>> import bizpack as bp
    >>> bp.clean_file("dirty_sales.csv")
    """
    input_p = Path(input_path)
    if not input_p.exists():
        raise FileNotFoundError(f"File not found: '{input_path}'")

    ext = input_p.suffix.lower()
    if ext in (".xlsx", ".xls", ".xlsm"):
        df = read_excel(input_p, target_currency=target_currency, **kwargs)
    else:
        df = read_csv(input_p, target_currency=target_currency, **kwargs)

    # Determine default output path if not provided
    if output_path is None:
        curr_suffix = ""
        if "currency_conversions" in df.attrs:
            for audit in df.attrs["currency_conversions"].values():
                curr_suffix = f"_{audit['target_currency'].lower()}"
                break
        output_p = input_p.parent / f"clean_{input_p.stem}{curr_suffix}{ext}"
    else:
        output_p = Path(output_path)

    # Save to new clean file
    if ext in (".xlsx", ".xls", ".xlsm"):
        df.to_excel(output_p, index=False)
    else:
        df.to_csv(output_p, index=False)

    print(f"\n[BizPack] Success! Clean file created: {output_p.name}")
    print(f"Location: {output_p.resolve()}")
    print(f"Records: {len(df):,} rows | Columns cleaned: {len(df.columns)}")
    return df

