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


def test_mixed_dates_in_same_column_with_partner_context():
    """
    Test a column with a mixture of Indian (DD/MM/YYYY) and US (MM/DD/YYYY) dates.
    Ensures:
    1. Unambiguous dates like 25/03/2024 and 03/25/2024 are both parsed to March 25th with ZERO NaTs.
    2. Ambiguous dates like 05/09/2024 are resolved row-by-row using partner context:
       - Row with INR / India -> September 5th
       - Row with USD / North America -> May 9th
    3. Ambiguous dates like 01/02/2024:
       - Row with EUR / Europe -> February 1st
       - Row with USD / USA -> January 2nd
    """
    df = pd.DataFrame({
        "order_date": [
            "25/03/2024",  # Indian unambiguous
            "03/25/2024",  # US unambiguous
            "05/09/2024",  # Indian ambiguous -> Sept 5
            "05/09/2024",  # US ambiguous -> May 9
            "31-12-2023",  # Indian unambiguous
            "12-31-2023",  # US unambiguous
            "01/02/2024",  # Europe ambiguous -> Feb 1
            "01/02/2024",  # US ambiguous -> Jan 2
        ],
        "amount": [
            "₹ 5,000",
            "$ 100",
            "₹ 8,900",
            "$ 250",
            "₹ 15,000",
            "$ 400",
            "€ 500",
            "$ 500",
        ],
        "region": [
            "India",
            "USA",
            "India",
            "North America",
            "APAC",
            "USA",
            "Europe",
            "USA",
        ],
    })

    cleaned = bp.clean(df, target_currency="INR")

    # Column should be converted to datetime64 with ZERO NaT drops
    assert np.issubdtype(cleaned["order_date"].dtype, np.datetime64)
    assert cleaned["order_date"].isna().sum() == 0

    # Row 0: 25/03/2024 -> March 25, 2024
    assert cleaned["order_date"].iloc[0] == pd.Timestamp("2024-03-25")
    # Row 1: 03/25/2024 -> March 25, 2024 (US date preserved without turning into NaT!)
    assert cleaned["order_date"].iloc[1] == pd.Timestamp("2024-03-25")
    # Row 2: 05/09/2024 in India row -> September 5, 2024
    assert cleaned["order_date"].iloc[2] == pd.Timestamp("2024-09-05")
    # Row 3: 05/09/2024 in US row -> May 9, 2024
    assert cleaned["order_date"].iloc[3] == pd.Timestamp("2024-05-09")
    # Row 4: 31-12-2023 -> December 31, 2023
    assert cleaned["order_date"].iloc[4] == pd.Timestamp("2023-12-31")
    # Row 5: 12-31-2023 -> December 31, 2023
    assert cleaned["order_date"].iloc[5] == pd.Timestamp("2023-12-31")
    # Row 6: 01/02/2024 in Europe row -> February 1, 2024
    assert cleaned["order_date"].iloc[6] == pd.Timestamp("2024-02-01")
    # Row 7: 01/02/2024 in US row -> January 2, 2024
    assert cleaned["order_date"].iloc[7] == pd.Timestamp("2024-01-02")

    # Verify audit info recorded mixed date detection
    audit = cleaned.attrs["date_formats"]["order_date"]
    assert audit["is_mixed"] is True
    assert audit["ambiguous_resolved_by_row_context"] >= 4


def test_mixed_dates_standalone_series():
    """
    Test mixed dates on a standalone pd.Series with no other columns.
    Both 25/03/2024 (Indian) and 03/25/2024 (US) must parse successfully to March 25th.
    """
    s = pd.Series(["25/03/2024", "03/25/2024", "2024-01-15", "15-Aug-2024"])
    parsed, audit = parse_dates_consistently(s)

    assert parsed.isna().sum() == 0
    assert parsed.iloc[0] == pd.Timestamp("2024-03-25")
    assert parsed.iloc[1] == pd.Timestamp("2024-03-25")
    assert parsed.iloc[2] == pd.Timestamp("2024-01-15")
    assert parsed.iloc[3] == pd.Timestamp("2024-08-15")
    assert audit["is_mixed"] is True

