"""
International currency detection, standardization, and conversion module for BizPack.
Prevents catastrophic financial calculation errors when datasets contain mixed currencies
(e.g., USD, INR, EUR, GBP, JPY).
"""

from typing import Dict, List, Optional, Set, Tuple, Union, Any
import re
import sys
import numpy as np
import pandas as pd

# Mapping of currency symbols & common prefixes to ISO 4217 3-letter codes
SYMBOL_TO_CODE: Dict[str, str] = {
    "US$": "USD",
    "C$": "CAD",
    "CA$": "CAD",
    "A$": "AUD",
    "AU$": "AUD",
    "NZ$": "NZD",
    "R$": "BRL",
    "RS.": "INR",
    "RS": "INR",
    "₹": "INR",
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₩": "KRW",
    "₺": "TRY",
    "₽": "RUB",
    "₴": "UAH",
    "₫": "VND",
    "฿": "THB",
    "₱": "PHP",
    "₪": "ILS",
    "zł": "PLN",
    "Kč": "CZK",
    "Ft": "HUF",
    "CHF": "CHF",
    "kr": "SEK",
}

# Mapping of ISO codes to primary presentation symbols
CODE_TO_SYMBOL: Dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "CAD": "CA$",
    "AUD": "A$",
    "JPY": "¥",
    "CHF": "CHF ",
    "CNY": "¥",
    "BRL": "R$",
    "MXN": "Mex$",
    "SGD": "S$",
    "AED": "AED ",
    "KRW": "₩",
    "SEK": "kr ",
    "RUB": "₽",
    "TRY": "₺",
    "PLN": "zł ",
    "ILS": "₪",
}

# Standard baseline exchange rates (relative to 1.0 USD)
# Default values based on recent international market averages
DEFAULT_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,           # 1 EUR = 1.08 USD
    "GBP": 1.28,           # 1 GBP = 1.28 USD
    "INR": 1.0 / 89.0,     # 1 USD = 89.0 INR (1 INR = ~0.01124 USD)
    "CAD": 0.74,           # 1 CAD = 0.74 USD
    "AUD": 0.66,           # 1 AUD = 0.66 USD
    "JPY": 1.0 / 150.0,    # 1 JPY = ~0.00667 USD
    "CHF": 1.14,           # 1 CHF = 1.14 USD
    "CNY": 1.0 / 7.20,     # 1 CNY = ~0.1389 USD
    "BRL": 1.0 / 5.50,     # 1 BRL = ~0.1818 USD
    "MXN": 1.0 / 18.50,    # 1 MXN = ~0.054 USD
    "SGD": 0.75,           # 1 SGD = 0.75 USD
    "AED": 0.272,          # 1 AED = 0.272 USD
    "SEK": 1.0 / 10.50,
    "KRW": 1.0 / 1350.0,
    "TRY": 1.0 / 34.0,
    "RUB": 1.0 / 92.0,
    "PLN": 0.25,
    "CZK": 0.043,
    "HUF": 0.0028,
    "ILS": 0.27,
    "THB": 1.0 / 36.0,
    "PHP": 1.0 / 57.0,
    "VND": 1.0 / 25000.0,
}


def detect_currency(val: Any) -> Optional[str]:
    """
    Detect the currency ISO code from a string value or cell.
    Handles symbols ($, €, £, ₹, ¥), abbreviations (Rs., Rs, C$, A$), and ISO codes (USD, INR, EUR).
    
    Examples:
    >>> detect_currency('$1,200.00') -> 'USD'
    >>> detect_currency('₹ 90,000') -> 'INR'
    >>> detect_currency('Rs. 5,000') -> 'INR'
    >>> detect_currency('1.250,50 €') -> 'EUR'
    >>> detect_currency('100 GBP') -> 'GBP'
    """
    if pd.isna(val) or val is None:
        return None

    s = str(val).strip()
    if not s:
        return None

    s_upper = s.upper()

    # 1. Check unique unicode symbols
    if "₹" in s:
        return "INR"
    if "€" in s:
        return "EUR"
    if "£" in s:
        return "GBP"
    if "¥" in s:
        return "JPY"
    if "₩" in s:
        return "KRW"
    if "₺" in s:
        return "TRY"
    if "₽" in s:
        return "RUB"
    if "₴" in s:
        return "UAH"
    if "₫" in s:
        return "VND"
    if "฿" in s:
        return "THB"
    if "₱" in s:
        return "PHP"
    if "₪" in s:
        return "ILS"
    if "zł" in s:
        return "PLN"
    if "Kč" in s:
        return "CZK"
    if "Ft" in s:
        return "HUF"

    # 2. Check Indian Rupee textual variants (Rs. or Rs followed by digits)
    if re.search(r"\bRS\.?\s*\d", s, re.IGNORECASE) or re.search(r"\d\s*RS\.?\b", s, re.IGNORECASE):
        return "INR"

    # 3. Check specific multi-char currency prefixes
    if "US$" in s_upper:
        return "USD"
    if "C$" in s_upper or "CA$" in s_upper:
        return "CAD"
    if "A$" in s_upper or "AU$" in s_upper:
        return "AUD"
    if "NZ$" in s_upper:
        return "NZD"
    if "R$" in s_upper:
        return "BRL"

    # 4. Standard Dollar sign
    if "$" in s:
        return "USD"

    # 5. Check 3-letter ISO codes (as separate word token)
    for code in DEFAULT_RATES_TO_USD.keys():
        if re.search(rf"\b{code}\b", s_upper):
            return code

    return None


def detect_header_currency(col_name: str) -> Optional[str]:
    """
    Detect if a column header specifies a currency (e.g. 'gross_revenue_usd', 'Sales ($)', 'Revenue (INR)').
    """
    return detect_currency(col_name)


def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str,
    rates: Optional[Dict[str, float]] = None,
) -> float:
    """
    Convert an amount from one currency to another using exchange rates.
    All rates are expressed relative to 1.0 USD.

    Example:
    >>> convert_amount(100.0, from_currency='USD', to_currency='INR') -> 8900.0
    >>> convert_amount(8900.0, from_currency='INR', to_currency='USD') -> 100.0
    >>> convert_amount(100.0, from_currency='EUR', to_currency='INR') -> 9612.0
    """
    if pd.isna(amount) or amount is None:
        return np.nan

    from_curr = from_currency.upper().strip()
    to_curr = to_currency.upper().strip()

    if from_curr == to_curr:
        return round(float(amount), 2)

    active_rates = dict(DEFAULT_RATES_TO_USD)
    if rates:
        active_rates.update({k.upper().strip(): float(v) for k, v in rates.items()})

    if from_curr not in active_rates:
        raise ValueError(
            f"Unknown exchange rate for source currency: '{from_curr}'. "
            f"Supported currencies: {', '.join(sorted(active_rates.keys()))}. "
            f"You can provide custom rates via rates={{'{from_curr}': rate_to_usd}}."
        )
    if to_curr not in active_rates:
        raise ValueError(
            f"Unknown exchange rate for target currency: '{to_curr}'. "
            f"Supported currencies: {', '.join(sorted(active_rates.keys()))}. "
            f"You can provide custom rates via rates={{'{to_curr}': rate_to_usd}}."
        )

    # Convert source -> USD -> target
    amount_in_usd = float(amount) * active_rates[from_curr]
    amount_in_target = amount_in_usd / active_rates[to_curr]

    return round(amount_in_target, 2)


def ask_user_target_currency(
    detected_currencies: List[str],
    col_name: str = "",
    default: str = "USD",
) -> str:
    """
    Prompt the user directly in the output area when multiple currencies are detected.
    Allows user to select their desired target currency (e.g. INR, USD, EUR, GBP).
    """
    sorted_curr = sorted(list(set(detected_currencies)))
    curr_list_str = ", ".join(sorted_curr)

    print("\n" + "=" * 75)
    col_disp = f" in column '{col_name}'" if col_name else ""
    print(f" [BizPack Alert] Multiple currencies detected{col_disp}: [{curr_list_str}]")
    print(" To prevent financial errors, BizPack standardizes all amounts into 1 currency.")
    print("=" * 75)
    prompt_msg = f" Which currency would you like to convert everything into? ({curr_list_str}) [Default: {default}]: "

    try:
        user_choice = input(prompt_msg).strip().upper()
        if user_choice:
            if user_choice in DEFAULT_RATES_TO_USD or user_choice in sorted_curr:
                print(f" -> Standardizing all values to: {user_choice}\n" + "=" * 75 + "\n")
                return user_choice
            else:
                print(f" -> '{user_choice}' not recognized. Using default: {default}\n" + "=" * 75 + "\n")
                return default
        else:
            print(f" -> Using default: {default}\n" + "=" * 75 + "\n")
            return default
    except (EOFError, OSError, KeyboardInterrupt):
        # Fallback for headless non-interactive environments or closed pipes
        print(f" [Notice] Non-interactive environment. Standardizing to '{default}'.")
        print("=" * 75 + "\n")
        return default



def standardize_currency_series(
    series: pd.Series,
    target_currency: Optional[str] = None,
    rates: Optional[Dict[str, float]] = None,
    col_name: str = "",
    default_currency: str = "USD",
    prompt_if_interactive: bool = True,
) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
    """
    Scan a Series with mixed currencies, standardize all values into target_currency,
    and return (converted_numeric_series, original_currencies_series, audit_dict).
    
    If multiple currencies exist and target_currency is not specified:
    - Prompts the user if interactive (or standardizes to dominant/default).
    """
    from bizpack.cleaner import _parse_business_number

    # 1. Parse each cell's numeric value and currency symbol
    amounts: List[Optional[float]] = []
    detected_list: List[Optional[str]] = []

    header_curr = detect_header_currency(col_name) if col_name else None

    for val in series:
        if pd.isna(val) or val is None:
            amounts.append(np.nan)
            detected_list.append(None)
            continue

        curr = detect_currency(val)
        num, _ = _parse_business_number(val)
        amounts.append(num)
        detected_list.append(curr)

    # 2. Determine column baseline currency for cells without an explicit symbol
    # Count observed currencies
    curr_counts: Dict[str, int] = {}
    for c in detected_list:
        if c:
            curr_counts[c] = curr_counts.get(c, 0) + 1

    if curr_counts:
        dominant_currency = max(curr_counts.items(), key=lambda x: x[1])[0]
    elif header_curr:
        dominant_currency = header_curr
    else:
        dominant_currency = default_currency

    # Fill unlabelled numeric cells with column's dominant currency
    resolved_currencies: List[str] = []
    for num, curr in zip(amounts, detected_list):
        if num is not None and not pd.isna(num):
            resolved_currencies.append(curr or dominant_currency)
        else:
            resolved_currencies.append("")

    unique_currencies = sorted(list(set(c for c in resolved_currencies if c)))

    # 3. Determine target currency
    final_target = target_currency
    if not final_target:
        if len(unique_currencies) > 1:
            if prompt_if_interactive:
                final_target = ask_user_target_currency(
                    unique_currencies,
                    col_name=col_name,
                    default=dominant_currency,
                )
            else:
                final_target = dominant_currency
        elif len(unique_currencies) == 1:
            final_target = unique_currencies[0]
        else:
            final_target = default_currency

    final_target = final_target.upper().strip()

    # 4. Perform conversion
    active_rates = dict(DEFAULT_RATES_TO_USD)
    if rates:
        active_rates.update({k.upper().strip(): float(v) for k, v in rates.items()})

    converted_values: List[Optional[float]] = []
    rates_used: Dict[str, float] = {}

    for amt, curr in zip(amounts, resolved_currencies):
        if amt is None or pd.isna(amt):
            converted_values.append(np.nan)
        elif curr:
            converted = convert_amount(amt, from_currency=curr, to_currency=final_target, rates=active_rates)
            converted_values.append(converted)
            # Record effective conversion factor: (from_rate / to_rate)
            if curr not in rates_used:
                rates_used[curr] = round(active_rates[curr] / active_rates[final_target], 6)
        else:
            converted_values.append(amt)

    audit_info: Dict[str, Any] = {
        "column": col_name,
        "target_currency": final_target,
        "detected_currencies": unique_currencies,
        "dominant_currency": dominant_currency,
        "effective_rates_to_target": rates_used,
        "rows_converted": sum(1 for c in resolved_currencies if c and c != final_target),
        "total_rows": len(series),
    }

    return (
        pd.Series(converted_values, index=series.index, dtype=float),
        pd.Series(resolved_currencies, index=series.index, dtype="string"),
        audit_info,
    )


def standardize_currency_df(
    df: pd.DataFrame,
    columns: Optional[Union[str, List[str]]] = None,
    target_currency: Optional[str] = None,
    rates: Optional[Dict[str, float]] = None,
    prompt_if_interactive: bool = True,
    keep_currency_col: bool = False,
) -> pd.DataFrame:
    """
    Standardize currency columns across a DataFrame into a single requested currency.
    If columns is None, auto-detects all columns containing currency symbols or codes.
    
    Example:
    >>> clean_df = standardize_currency_df(df, target_currency='INR')
    >>> clean_df = standardize_currency_df(df, columns=['revenue', 'cost'], target_currency='USD')
    """
    df = df.copy()

    # Determine columns to inspect
    if columns is not None:
        target_cols = [columns] if isinstance(columns, str) else list(columns)
    else:
        # Auto-detect columns with currency symbols
        target_cols = []
        for col in df.columns:
            # Check string/object columns
            if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                sample = df[col].dropna().head(100)
                curr_count = sum(1 for v in sample if detect_currency(v) is not None)
                if curr_count > 0:
                    target_cols.append(col)

    if not target_cols:
        return df

    conversions_meta = {}

    for col in target_cols:
        if col not in df.columns:
            continue

        converted_series, orig_curr_series, audit = standardize_currency_series(
            df[col],
            target_currency=target_currency,
            rates=rates,
            col_name=str(col),
            prompt_if_interactive=prompt_if_interactive,
        )

        df[col] = converted_series
        conversions_meta[col] = audit

        if keep_currency_col:
            df[f"{col}_original_currency"] = orig_curr_series

    if "currency_conversions" not in df.attrs:
        df.attrs["currency_conversions"] = {}
    df.attrs["currency_conversions"].update(conversions_meta)

    return df
