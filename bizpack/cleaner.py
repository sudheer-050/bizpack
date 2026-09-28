"""
Core data cleaning module for BizKit.
Zero-friction spreadsheet and business data hygiene.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
import re
import os
import unicodedata
import warnings
import numpy as np
import pandas as pd

from bizpack._parsing import (
    CURRENCY_SYMBOLS,
    parse_business_number as _parse_business_number,
)
from bizpack.currency import (
    standardize_currency_series,
    detect_currency,
    detect_header_currency,
)
from bizpack.dates import parse_dates_consistently

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
        # Replace NaN/NaT with None so attrs stay JSON-serializable for downstream consumers (e.g. Streamlit).
        totals_records = [
            {k: (None if pd.isna(v) else v) for k, v in record.items()}
            for record in totals_records
        ]
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
    # Whole-name matches or "_"-delimited suffixes only, so words that merely end in
    # these letters (e.g. "valid", "paid", "avoid") aren't misclassified as ID columns.
    id_names = ("id", "zip", "zipcode", "ssn", "ein", "phone", "account", "code", "num", "no")
    id_suffixes = tuple(f"_{name}" for name in id_names)
    if name_lower in id_names or name_lower.endswith(id_suffixes):
        return True

    # Check for leading zeros in non-null strings
    non_nulls = series.dropna().astype(str).tolist()
    if not non_nulls:
        return False

    leading_zero_count = sum(1 for val in non_nulls if len(val) > 1 and val.startswith("0") and val.isdigit())
    if leading_zero_count / len(non_nulls) >= 0.2:
        return True

    return False


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
    raw_df = df.copy()
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

        # Check if this column represents currency data (computed regardless of
        # the strict threshold below, so a column that's clearly currency but
        # has a few stray unparseable values -- e.g. a typo'd/unsupported symbol
        # variant -- doesn't get silently dumped back as raw, unconverted text).
        has_currency = (
            (type_votes.get("currency", 0) > 0)
            or any(detect_currency(v) is not None for v in sample.head(25))
            or (detect_header_currency(str(col)) is not None)
        )

        # A column passes if it's dominantly numeric (the strict threshold), OR
        # it has clear currency evidence and is still majority-parseable -- in
        # that case we still convert it and let standardize_currency_series's
        # own unparsed-value tracking flag the minority that failed, instead of
        # bypassing the whole column with zero conversion and zero audit trail.
        if match_ratio >= threshold or (has_currency and match_ratio >= 0.5):
            dominant_type = max(type_votes.items(), key=lambda x: x[1])[0] if type_votes else "number"
            formats_meta[col] = dominant_type

            if dominant_type in ("percent", "percentage"):
                # Record the exact ratio mode used during parsing, so
                # format_for_display() can restore it deterministically instead
                # of re-guessing from the data (a value-range heuristic like
                # "max abs <= 1.0" breaks on legitimate ratio columns that
                # contain a >100% value, e.g. 1.50 for "150%").
                if "_percent_ratio_mode" not in df.attrs:
                    df.attrs["_percent_ratio_mode"] = {}
                df.attrs["_percent_ratio_mode"][col] = percent_as_ratio

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
            unparsed_count = 0
            unparsed_samples: List[str] = []

            def _coerce(val):
                nonlocal unparsed_count
                num, _ = _parse_business_number(val, percent_as_ratio=percent_as_ratio)
                if num is None:
                    if pd.notna(val):
                        unparsed_count += 1
                        if len(unparsed_samples) < 5:
                            unparsed_samples.append(str(val))
                    return np.nan
                return num

            df[col] = df[col].map(_coerce).astype(float)

            if unparsed_count:
                if "numeric_coercion_issues" not in df.attrs:
                    df.attrs["numeric_coercion_issues"] = {}
                df.attrs["numeric_coercion_issues"][col] = {
                    "unparsed_count": unparsed_count,
                    "unparsed_samples": unparsed_samples,
                }
            continue

        # 2. Test for Boolean Columns (e.g. Y/N, Yes/No, True/False, 1/0)
        # "1"/"0" are only included here (not in the Business Numeric test above)
        # because reaching this point already means the column failed the
        # numeric-dominant threshold test -- i.e. it is NOT a plain numeric/count
        # column, so a stray "1"/"0" mixed in with yes/no/true/false tokens is
        # safe to treat as boolean rather than being silently left unconverted.
        lower_vals = sample.astype(str).str.lower().str.strip()
        bool_map = {
            "y": True, "yes": True, "true": True, "t": True, "1": True,
            "n": False, "no": False, "false": False, "f": False, "0": False,
        }
        unique_lower = set(lower_vals.unique())
        if unique_lower.issubset(bool_map.keys()) and len(unique_lower) > 0:
            df[col] = df[col].astype(str).str.lower().str.strip().map(bool_map).astype("boolean")
            formats_meta[col] = "boolean"
            continue

        # 3. Test for Datetime (with column-wide format deduction from other entries)
        try:
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
                        df=raw_df,
                    )
                    df[col] = parsed_series
                    formats_meta[col] = "datetime"
                    if "date_formats" not in df.attrs:
                        df.attrs["date_formats"] = {}
                    df.attrs["date_formats"][col] = date_audit
                    continue
        except Exception as exc:
            # Date detection is a best-effort heuristic over arbitrary user data; leave the
            # column untouched on failure, but surface *why* rather than failing silently.
            warnings.warn(
                f"[BizPack] Skipped date detection for column '{col}': {exc!r}",
                RuntimeWarning,
                stacklevel=2,
            )

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


def _resolve_filepath(path_or_str: Any) -> Any:
    if isinstance(path_or_str, (str, Path)):
        p = Path(path_or_str)
        if p.exists():
            return p
        import inspect
        frame = inspect.currentframe()
        try:
            while frame:
                fname = frame.f_code.co_filename
                if fname and os.path.exists(fname) and not fname.startswith("<") and "cleaner.py" not in fname:
                    cand = Path(fname).parent / path_or_str
                    if cand.exists():
                        return cand
                frame = frame.f_back
        finally:
            del frame
    return path_or_str


def _pop_clean_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Pop and return the `clean()` keyword arguments embedded in a read_csv/read_excel call."""
    return {
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


def read_csv(filepath_or_buffer: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Read a CSV file safely and automatically clean it with BizPack.
    Supports currency standardization via target_currency='USD' or 'INR'.
    Automatically deduces date format (DD/MM/YYYY vs MM/DD/YYYY) from column entries and currency.
    Pass clean=False to read the raw dirty DataFrame.
    """
    clean_kwargs = _pop_clean_kwargs(kwargs)
    clean_data = kwargs.pop("clean", True)
    if "dtype" not in kwargs and clean_data:
        kwargs["dtype"] = str

    resolved_path = _resolve_filepath(filepath_or_buffer)
    df = pd.read_csv(resolved_path, **kwargs)
    if not clean_data:
        return df
    return clean(df, **clean_kwargs)


def read_excel(filepath_or_buffer: Any, **kwargs: Any) -> pd.DataFrame:
    """
    Read an Excel file safely and automatically clean it with BizPack.
    Supports currency standardization via target_currency='USD' or 'INR'.
    Automatically deduces date format (DD/MM/YYYY vs MM/DD/YYYY) from column entries and currency.
    """
    clean_kwargs = _pop_clean_kwargs(kwargs)
    clean_data = kwargs.pop("clean", True)
    if "dtype" not in kwargs and clean_data:
        kwargs["dtype"] = str
    resolved_path = _resolve_filepath(filepath_or_buffer)
    df = pd.read_excel(resolved_path, **kwargs)
    if not clean_data:
        return df
    return clean(df, **clean_kwargs)


def clean_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    target_currency: Optional[str] = None,
    verbose: bool = True,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Clean an entire spreadsheet file in ONE line.
    Automatically detects CSV vs Excel, standardizes mixed currencies by prompting
    in the output area, and saves to a brand new file without touching the original.

    Pass verbose=False to suppress the "Success!" console summary (useful when calling
    clean_file() from an automated pipeline/script).

    Example:
    >>> import bizpack as bp
    >>> bp.clean_file("dirty_sales.csv")
    """
    input_p = Path(_resolve_filepath(input_path))
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
        out_cand = Path(output_path)
        output_p = input_p.parent / out_cand if not out_cand.is_absolute() and len(out_cand.parts) == 1 else out_cand

    # Save to new clean file
    if ext in (".xlsx", ".xls", ".xlsm"):
        df.to_excel(output_p, index=False)
    else:
        df.to_csv(output_p, index=False)

    if verbose:
        print(f"\n[BizPack] Success! Clean file created: {output_p.name}")
        print(f"Location: {output_p.resolve()}")
        print(f"Records: {len(df):,} rows | Columns cleaned: {len(df.columns)}")
    return df

