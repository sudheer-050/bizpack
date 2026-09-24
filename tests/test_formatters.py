import pandas as pd
from bizkit import formatters


def test_format_currency():
    s = pd.Series([1250.5, -45.0, 0.0, None])
    formatted = formatters.format_currency(s, symbol="$", decimals=2)
    assert formatted.iloc[0] == "$1,250.50"
    assert formatted.iloc[1] == "-$45.00"
    assert formatted.iloc[2] == "$0.00"
    assert formatted.iloc[3] == ""


def test_format_percent():
    s_ratio = pd.Series([0.154, 0.02, 1.0])
    formatted = formatters.format_percent(s_ratio, decimals=1, is_ratio=True)
    assert formatted.iloc[0] == "15.4%"
    assert formatted.iloc[1] == "2.0%"
    assert formatted.iloc[2] == "100.0%"


def test_format_accounting():
    s = pd.Series([1200.0, -450.5, 0.0])
    formatted = formatters.format_accounting(s, symbol="$", decimals=2)
    assert formatted.iloc[0] == "$1,200.00"
    assert formatted.iloc[1] == "($450.50)"
    assert formatted.iloc[2] == "—"


def test_format_for_display():
    df = pd.DataFrame({
        "revenue": [1000.0, 2500.5],
        "margin": [0.15, 0.22],
        "net_income": [-150.0, 300.0]
    })
    df.attrs["_biz_formats"] = {
        "revenue": "currency",
        "margin": "percentage",
        "net_income": "accounting"
    }
    
    display_df = formatters.format_for_display(df)
    assert display_df["revenue"].iloc[0] == "$1,000.00"
    assert display_df["margin"].iloc[0] == "15.0%"
    assert display_df["net_income"].iloc[0] == "($150.00)"
    assert display_df["net_income"].iloc[1] == "$300.00"
