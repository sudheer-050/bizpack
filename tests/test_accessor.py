import pandas as pd
import bizkit  # Register accessor


def test_accessor_clean_and_format():
    df = pd.DataFrame({
        " Product Name ": ["Widget A", "Widget B", "Total"],
        " Price ($) ": ["$100.00", "$250.50", "$350.50"]
    })
    
    # Test df.biz.clean()
    clean_df = df.biz.clean()
    assert list(clean_df.columns) == ["product_name", "price"]
    assert len(clean_df) == 2
    assert clean_df["price"].iloc[0] == 100.0

    # Test df.biz.format()
    display_df = clean_df.biz.format()
    assert display_df["price"].iloc[0] == "$100.00"


def test_accessor_pareto():
    df = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "sales": [1000, 500, 200, 100]
    })
    pareto_df = df.biz.pareto(dim_col="region", metric_col="sales")
    assert "is_top_80" in pareto_df.columns
    assert bool(pareto_df["is_top_80"].iloc[0]) is True
