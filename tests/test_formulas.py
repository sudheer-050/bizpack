import numpy as np
import pandas as pd
import pytest
from bizpack import formulas


def test_xlookup_series():
    sales = pd.DataFrame({"sku": ["A1", "B2", "C3", "A1", "D4"]})
    catalog = pd.DataFrame({
        "product_code": ["A1", "B2", "C3"],
        "price": [10.5, 25.0, 5.0]
    })
    
    res = formulas.xlookup(sales["sku"], catalog["product_code"], catalog["price"], default=0.0)
    assert list(res) == [10.5, 25.0, 5.0, 10.5, 0.0]


def test_xlookup_scalar():
    catalog = pd.DataFrame({
        "code": ["US", "CA", "UK"],
        "rate": [1.0, 0.75, 1.25]
    })
    val = formulas.xlookup("CA", catalog["code"], catalog["rate"])
    assert val == 0.75
    val_missing = formulas.xlookup("FR", catalog["code"], catalog["rate"], default=0.0)
    assert val_missing == 0.0


def test_growth():
    dates = pd.date_range("2024-01-01", periods=3, freq="MS")
    df = pd.DataFrame({
        "order_date": dates,
        "revenue": [100.0, 150.0, 120.0]
    })
    g_df = formulas.growth(df, date_col="order_date", metric_col="revenue", freq="M")
    
    assert len(g_df) == 3
    assert pd.isna(g_df["growth_pct"].iloc[0])
    assert g_df["delta_revenue"].iloc[1] == 50.0
    assert g_df["growth_pct"].iloc[1] == 50.0
    assert g_df["delta_revenue"].iloc[2] == -30.0
    assert pytest.approx(g_df["growth_pct"].iloc[2], 0.1) == -20.0


def test_pareto():
    df = pd.DataFrame({
        "client": ["A", "B", "C", "D", "E"],
        "revenue": [500, 300, 100, 50, 50]  # Total = 1000
    })
    p_df = formulas.pareto(df, dim_col="client", metric_col="revenue", top_pct=0.80)
    
    # Client A (50%) + Client B (30%) = 80%
    assert bool(p_df["is_top_80"].iloc[0]) is True
    assert bool(p_df["is_top_80"].iloc[1]) is True
    assert bool(p_df["is_top_80"].iloc[2]) is False
    assert "summary" in p_df.attrs


def test_run_rate():
    dates = [
        pd.Timestamp("2024-03-01"),
        pd.Timestamp("2024-03-05"),
        pd.Timestamp("2024-03-10"),
    ]
    df = pd.DataFrame({
        "date": dates,
        "sales": [1000, 2000, 3000]
    })
    # Total sales to March 10 = 6000 across 10 days = 600/day
    # March has 31 days -> Projected = 600 * 31 = 18,600
    rr = formulas.run_rate(df, date_col="date", metric_col="sales", target=20000, period="M")
    assert rr["actual_to_date"].iloc[0] == 6000.0
    assert rr["days_elapsed"].iloc[0] == 10
    assert rr["total_days"].iloc[0] == 31
    assert rr["projected_run_rate"].iloc[0] == 18600.0
    assert pytest.approx(rr["pacing_pct"].iloc[0], 0.1) == 93.0
