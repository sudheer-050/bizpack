import numpy as np
import pandas as pd
import pytest
from bizpack import cleaner


def test_clean_headers():
    df = pd.DataFrame(columns=[" Customer ID / Ref# ", "Total ($)", "sales", "sales", "Order.Date"])
    cleaned = cleaner.clean_headers(df)
    assert list(cleaned.columns) == ["customer_id_ref", "total", "sales", "sales_1", "order_date"]


def test_drop_empty():
    df = pd.DataFrame({
        "a": [1, np.nan, np.nan],
        "b": ["x", np.nan, np.nan],
        "c": [np.nan, np.nan, np.nan]
    })
    cleaned = cleaner.drop_empty(df)
    assert cleaned.shape == (1, 2)
    assert list(cleaned.columns) == ["a", "b"]
    assert cleaned.iloc[0]["a"] == 1


def test_strip_totals():
    df = pd.DataFrame({
        "item": ["Widget A", "Widget B", "Grand Total"],
        "sales": [100, 200, 300]
    })
    cleaned = cleaner.strip_totals(df)
    assert len(cleaned) == 2
    assert "Grand Total" not in cleaned["item"].values
    assert "totals" in cleaned.attrs
    assert len(cleaned.attrs["totals"]) == 1


def test_clean_strings():
    df = pd.DataFrame({
        "text": ["  Acme Corp \xa0", "-", "N/A", "Valid Text"],
        "num": [1, 2, 3, 4]
    })
    cleaned = cleaner.clean_strings(df)
    assert cleaned["text"].iloc[0] == "Acme Corp"
    assert pd.isna(cleaned["text"].iloc[1])
    assert pd.isna(cleaned["text"].iloc[2])
    assert cleaned["text"].iloc[3] == "Valid Text"


def test_clean_types_currency_and_accounting():
    df = pd.DataFrame({
        "revenue": ["$1,250.00", "€ 500.50", "$ (200.00)", "-$ 50.00"],
        "margin": ["15.4%", "(2.5%)", "0.0%", "50%"],
        "zip_code": ["07001", "00421", "08540", "01234"]
    })
    cleaned = cleaner.clean_types(df, percent_as_ratio=True)
    
    # Revenue should be float
    assert np.issubdtype(cleaned["revenue"].dtype, np.floating)
    assert cleaned["revenue"].iloc[0] == 1250.0
    assert cleaned["revenue"].iloc[1] == 500.5
    assert cleaned["revenue"].iloc[2] == -200.0
    assert cleaned["revenue"].iloc[3] == -50.0

    # Margin should be ratio float
    assert np.issubdtype(cleaned["margin"].dtype, np.floating)
    assert pytest.approx(cleaned["margin"].iloc[0], 0.0001) == 0.154
    assert pytest.approx(cleaned["margin"].iloc[1], 0.0001) == -0.025

    # Zip code MUST remain string with leading zeros intact
    assert cleaned["zip_code"].iloc[0] == "07001"
    assert cleaned["zip_code"].iloc[1] == "00421"


def test_clean_international_currencies():
    df = pd.DataFrame({
        "euro_standard": ["1.250,50 €", "€ 500,00", "(1.250,50 €)", "1 250,50 EUR"],
        "mixed_currency": ["$1,000.50", "£ 2,500.00", "CHF 1'250.50", "¥ 150,000"],
        "euro_decimals": ["1250,50", "45,99", "1.000.000", "0,75"]
    })
    cleaned = cleaner.clean_types(df)

    # European Euro column
    assert cleaned["euro_standard"].iloc[0] == 1250.5
    assert cleaned["euro_standard"].iloc[1] == 500.0
    assert cleaned["euro_standard"].iloc[2] == -1250.5
    assert cleaned["euro_standard"].iloc[3] == 1250.5

    # Mixed currencies
    assert cleaned["mixed_currency"].iloc[0] == 1000.5
    assert cleaned["mixed_currency"].iloc[1] == 2500.0
    assert cleaned["mixed_currency"].iloc[2] == 1250.5
    assert cleaned["mixed_currency"].iloc[3] == 150000.0

    # Euro decimals without currency symbol
    assert cleaned["euro_decimals"].iloc[0] == 1250.5
    assert cleaned["euro_decimals"].iloc[1] == 45.99
    assert cleaned["euro_decimals"].iloc[2] == 1000000.0
    assert cleaned["euro_decimals"].iloc[3] == 0.75


def test_clean_types_booleans():
    df = pd.DataFrame({
        "is_active": ["Y", "N", "Yes", "No"],
        "churned": ["true", "false", "TRUE", "FALSE"]
    })
    cleaned = cleaner.clean_types(df)
    assert cleaned["is_active"].iloc[0] is True or cleaned["is_active"].iloc[0] == 1
    assert cleaned["is_active"].iloc[1] is False or cleaned["is_active"].iloc[1] == 0


def test_master_clean():
    dirty_data = {
        " Customer Name ": ["Acme Inc", "Beta LLC", "Gamma Co", "Total"],
        " Revenue ($) ": ["$10,000.50", "($2,500.00)", "$5,000", "$12,500.50"],
        " Discount % ": ["5.0%", "10.0%", "-", "15%"],
        " Account_ID ": ["00123", "00456", "00789", "—"]
    }
    df = pd.DataFrame(dirty_data)
    cleaned = cleaner.clean(df)

    # Headers
    assert list(cleaned.columns) == ["customer_name", "revenue", "discount", "account_id"]
    
    # Total row removed
    assert len(cleaned) == 3
    assert "Total" not in cleaned["customer_name"].values

    # Numeric conversions
    assert cleaned["revenue"].iloc[0] == 10000.50
    assert cleaned["revenue"].iloc[1] == -2500.00
    assert cleaned["discount"].iloc[0] == 0.05
    assert pd.isna(cleaned["discount"].iloc[2])

    # ID preserved
    assert cleaned["account_id"].iloc[0] == "00123"
