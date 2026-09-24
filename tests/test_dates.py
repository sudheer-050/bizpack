"""
Unit tests for BizPack smart date inference and column-wide format deduction.
"""

import pandas as pd
import numpy as np
import pytest

import bizpack as bp
from bizpack.dates import infer_date_format_and_dayfirst, parse_dates_consistently


def test_infer_dayfirst_from_unambiguous_entries():
    # 25/09/2024 unambiguously has Day in the 1st position (25 > 12)
    s = pd.Series(["05/09/2024", "25/09/2024", "12/01/2024"])
    dayfirst, audit = infer_date_format_and_dayfirst(s)

    assert dayfirst is True
    assert audit["inferred_format"] == "DD/MM/YYYY"
    assert audit["day_first_votes"] == 1
    assert audit["month_first_votes"] == 0

    parsed, _ = parse_dates_consistently(s)
    # 05/09/2024 MUST be parsed as September 5th, not May 9th!
    assert parsed.iloc[0] == pd.Timestamp("2024-09-05")
    assert parsed.iloc[1] == pd.Timestamp("2024-09-25")
    assert parsed.iloc[2] == pd.Timestamp("2024-01-12")


def test_infer_monthfirst_from_unambiguous_entries():
    # 09/25/2024 unambiguously has Day in the 2nd position (25 > 12)
    s = pd.Series(["05/09/2024", "09/25/2024", "01/12/2024"])
    dayfirst, audit = infer_date_format_and_dayfirst(s)

    assert dayfirst is False
    assert audit["inferred_format"] == "MM/DD/YYYY"
    assert audit["month_first_votes"] == 1
    assert audit["day_first_votes"] == 0

    parsed, _ = parse_dates_consistently(s)
    # 05/09/2024 MUST be parsed as May 9th, not September 5th!
    assert parsed.iloc[0] == pd.Timestamp("2024-05-09")
    assert parsed.iloc[1] == pd.Timestamp("2024-09-25")
    assert parsed.iloc[2] == pd.Timestamp("2024-01-12")


def test_infer_date_from_currency_context_when_all_ambiguous():
    # All dates have part1 <= 12 and part2 <= 12 (ambiguous on their own)
    s = pd.Series(["05/09/2024", "06/07/2024"])

    # 1. When currency is INR (India), standard convention is DD/MM/YYYY
    dayfirst_inr, audit_inr = infer_date_format_and_dayfirst(s, dataset_currency="INR")
    assert dayfirst_inr is True
    assert audit_inr["inferred_format"] == "DD/MM/YYYY"

    parsed_inr, _ = parse_dates_consistently(s, dataset_currency="INR")
    assert parsed_inr.iloc[0] == pd.Timestamp("2024-09-05")  # September 5th

    # 2. When currency is EUR (Europe) or GBP (UK), standard convention is DD/MM/YYYY
    dayfirst_eur, _ = infer_date_format_and_dayfirst(s, dataset_currency="EUR")
    assert dayfirst_eur is True

    # 3. When currency is USD (US), standard convention is MM/DD/YYYY
    dayfirst_usd, audit_usd = infer_date_format_and_dayfirst(s, dataset_currency="USD")
    assert dayfirst_usd is False
    assert audit_usd["inferred_format"] == "MM/DD/YYYY"

    parsed_usd, _ = parse_dates_consistently(s, dataset_currency="USD")
    assert parsed_usd.iloc[0] == pd.Timestamp("2024-05-09")  # May 9th


def test_clean_df_with_smart_date_resolution():
    df = pd.DataFrame({
        "order_date": ["05/09/2024", "25/09/2024", "01/10/2024"],
        "revenue": ["₹8,900.00", "₹15,000.00", "₹20,000.00"],
    })

    cleaned = bp.clean(df, target_currency="INR")

    # Column should be converted to datetime64
    assert np.issubdtype(cleaned["order_date"].dtype, np.datetime64)

    # 05/09/2024 resolved as September 5th because 25/09 is DD/MM/YYYY and currency is INR
    assert cleaned["order_date"].iloc[0] == pd.Timestamp("2024-09-05")
    assert cleaned["order_date"].iloc[1] == pd.Timestamp("2024-09-25")
    assert cleaned["order_date"].iloc[2] == pd.Timestamp("2024-10-01")

    # Check audit information stored in attrs
    assert "date_formats" in cleaned.attrs
    assert cleaned.attrs["date_formats"]["order_date"]["dayfirst"] is True
