"""
Unit tests for BizPack international currency detection, standardization, and conversion.
"""

import sys
import numpy as np
import pandas as pd
import pytest

import bizpack as bp
from bizpack.currency import (
    detect_currency,
    convert_amount,
    standardize_currency_series,
    standardize_currency_df,
    ask_user_target_currency,
    DEFAULT_RATES_TO_USD,
)


def test_detect_currency_symbols():
    # Special symbols
    assert detect_currency("$1,200.00") == "USD"
    assert detect_currency("₹ 90,000") == "INR"
    assert detect_currency("₹8,900.00") == "INR"
    assert detect_currency("€500.00") == "EUR"
    assert detect_currency("1.250,50 €") == "EUR"
    assert detect_currency("£42,312.76") == "GBP"
    assert detect_currency("¥15,000") == "JPY"
    assert detect_currency("(€45,121.37)") == "EUR"

    # Rupee text variants
    assert detect_currency("Rs. 5,000") == "INR"
    assert detect_currency("Rs 5,000") == "INR"
    assert detect_currency("5000 Rs.") == "INR"

    # Dollar prefixes
    assert detect_currency("US$ 100") == "USD"
    assert detect_currency("C$ 100") == "CAD"
    assert detect_currency("CA$ 100") == "CAD"
    assert detect_currency("A$ 100") == "AUD"
    assert detect_currency("AU$ 100") == "AUD"
    assert detect_currency("R$ 500") == "BRL"

    # 3-letter ISO codes
    assert detect_currency("100 USD") == "USD"
    assert detect_currency("100 EUR") == "EUR"
    assert detect_currency("5000 INR") == "INR"
    assert detect_currency("100 CHF") == "CHF"

    # Non-currency values
    assert detect_currency("1,250.00") is None
    assert detect_currency("15.4%") is None
    assert detect_currency(None) is None
    assert detect_currency(np.nan) is None


def test_convert_amount_basic():
    # 1 USD = 89 INR (based on DEFAULT_RATES_TO_USD)
    assert convert_amount(100.0, "USD", "INR") == 8900.0
    assert convert_amount(8900.0, "INR", "USD") == 100.0

    # 1 EUR = 1.08 USD
    assert convert_amount(100.0, "EUR", "USD") == 108.0
    assert convert_amount(108.0, "USD", "EUR") == 100.0

    # EUR to INR: 100 EUR * 1.08 = 108 USD * 89 = 9612 INR
    assert convert_amount(100.0, "EUR", "INR") == 9612.0

    # Same currency
    assert convert_amount(250.50, "USD", "USD") == 250.50
    assert convert_amount(5000.0, "INR", "INR") == 5000.0

    # NaN / None
    assert np.isnan(convert_amount(np.nan, "USD", "INR"))


def test_convert_amount_custom_rates():
    # Override INR to 1 USD = 90 INR
    custom_rates = {"INR": 1.0 / 90.0}
    assert convert_amount(100.0, "USD", "INR", rates=custom_rates) == 9000.0
    assert convert_amount(9000.0, "INR", "USD", rates=custom_rates) == 100.0


def test_convert_amount_invalid_currency():
    with pytest.raises(ValueError, match="Unknown exchange rate"):
        convert_amount(100.0, "XYZ", "USD")
    with pytest.raises(ValueError, match="Unknown exchange rate"):
        convert_amount(100.0, "USD", "ABC")


def test_standardize_currency_series():
    # Series with mixed USD, INR, EUR, and GBP
    s = pd.Series(["$100.00", "₹8,900.00", "€100.00", "(£100.00)"])

    # Standardize to USD
    converted_usd, orig_curr, audit = standardize_currency_series(
        s, target_currency="USD", prompt_if_interactive=False
    )
    assert converted_usd.tolist() == [100.0, 100.0, 108.0, -128.0]
    assert orig_curr.tolist() == ["USD", "INR", "EUR", "GBP"]
    assert audit["target_currency"] == "USD"
    assert audit["rows_converted"] == 3

    # Standardize to INR
    converted_inr, orig_curr, audit = standardize_currency_series(
        s, target_currency="INR", prompt_if_interactive=False
    )
    assert converted_inr.tolist() == [8900.0, 8900.0, 9612.0, -11392.0]
    assert audit["target_currency"] == "INR"


def test_standardize_currency_with_unlabelled_cells():
    # Cells with no explicit currency should inherit column dominant currency (USD)
    s = pd.Series(["$100.00", "200.00", "₹8,900.00"])
    converted, orig_curr, audit = standardize_currency_series(
        s, target_currency="USD", prompt_if_interactive=False
    )
    # 200.00 is inferred as USD ($200)
    assert converted.tolist() == [100.0, 200.0, 100.0]
    assert orig_curr.tolist() == ["USD", "USD", "INR"]


def test_clean_df_with_target_currency():
    df = pd.DataFrame({
        "Customer": ["Acme Corp", "Beta LLC", "Gamma Ltd"],
        "Revenue": ["$100.00", "₹8,900.00", "€100.00"],
        "Quantity": ["10", "20", "30"],
        "Margin %": ["10.0%", "20.0%", "30.0%"],
    })

    # Clean to INR
    clean_df = bp.clean(df, target_currency="INR", keep_currency_col=True)

    # Revenue should be converted to INR
    assert clean_df["revenue"].tolist() == [8900.0, 8900.0, 9612.0]
    assert clean_df["revenue_original_currency"].tolist() == ["USD", "INR", "EUR"]

    # Quantity and Margin % should NOT be converted to currency
    assert clean_df["quantity"].tolist() == [10.0, 20.0, 30.0]
    assert clean_df["margin"].tolist() == [0.10, 0.20, 0.30]

    # Verify audit info in attrs
    assert "currency_conversions" in clean_df.attrs
    assert clean_df.attrs["currency_conversions"]["revenue"]["target_currency"] == "INR"


def test_interactive_user_prompt_choice(monkeypatch):
    # Simulate user typing 'INR' at interactive prompt
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "INR")

    s = pd.Series(["$100.00", "₹8,900.00"])
    converted, orig_curr, audit = standardize_currency_series(
        s, target_currency=None, col_name="sales", prompt_if_interactive=True
    )
    # Should standardize to INR based on simulated user input
    assert converted.tolist() == [8900.0, 8900.0]
    assert audit["target_currency"] == "INR"


def test_accessor_standardize_currency():
    df = pd.DataFrame({
        "sales": ["$100.00", "₹8,900.00", "€100.00"],
    })
    res = df.biz.standardize_currency("sales", target_currency="USD")
    assert res["sales"].tolist() == [100.0, 100.0, 108.0]


def test_format_currency_with_iso_codes():
    s = pd.Series([8900.0, -1250.50])
    formatted_inr = bp.format_currency(s, symbol="INR")
    assert formatted_inr.iloc[0] == "₹8,900.00"
    assert formatted_inr.iloc[1] == "-₹1,250.50"

    formatted_eur = bp.format_currency(s, symbol="EUR")
    assert formatted_eur.iloc[0] == "€8,900.00"

    formatted_usd = bp.format_currency(s, symbol="USD")
    assert formatted_usd.iloc[0] == "$8,900.00"
