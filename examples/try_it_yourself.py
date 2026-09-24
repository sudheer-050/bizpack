"""
BizPack - Try It Yourself Interactive Demo!
Run this script directly in your terminal:
    python try_it_yourself.py

This script:
1. Reads the dirty sales file without modifying it.
2. Interactively asks which currency you want (INR, USD, EUR, GBP, etc.).
3. Converts all mixed international transactions to your chosen currency.
4. Saves the result to a brand new file (e.g., clean_sales_inr.csv).
5. Shows a before-and-after comparison of converted rows.
"""

import sys
from pathlib import Path
import pandas as pd
import bizpack as bp

# Ensure UTF-8 output on Windows terminals (supports ₹, €, £)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    print("=" * 75)
    print("       BIZPACK INTERACTIVE CURRENCY & SPREADSHEET CLEANER       ")
    print("=" * 75)

    # 1. Ask the user for their preferred target currency
    print("\nWhich currency would you like to standardize your dataset to?")
    print("  1. INR (Indian Rupee - ₹)   [1 USD ≈ 89.0 INR]")
    print("  2. USD (US Dollar - $)       [Baseline 1.0 USD]")
    print("  3. EUR (Euro - €)            [1 EUR ≈ 1.08 USD]")
    print("  4. GBP (British Pound - £)   [1 GBP ≈ 1.28 USD]")

    user_input = input("\nEnter currency code (e.g., INR, USD, EUR) [Default: INR]: ").strip().upper()
    target_currency = user_input if user_input else "INR"

    print(f"\n-> Selected Target Currency: {target_currency}")

    # 2. Locate the dirty CSV file
    current_dir = Path(__file__).resolve().parent
    dirty_file = current_dir / "dirty_sales_1k.csv"
    if not dirty_file.exists():
        dirty_file = Path("dirty_sales_1k.csv")

    if not dirty_file.exists():
        print(f"Error: Could not find 'dirty_sales_1k.csv' in {current_dir}")
        return

    # 3. Read raw dirty file to preview BEFORE cleaning
    df_raw = pd.read_csv(dirty_file, dtype=str)
    print("\n" + "-" * 75)
    print("BEFORE CLEANING (Raw Dirty Data - Notice Mixed $, £, €, and raw numbers):")
    rev_col_raw = [c for c in df_raw.columns if "Revenue" in c][0]
    print(df_raw[[df_raw.columns[0], rev_col_raw]].head(5).to_string(index=False))
    print("-" * 75)

    # 4. Clean using BizPack and standardize currency (creates a new DataFrame)
    print(f"\nCleaning dataset and converting all currency values into {target_currency}...")
    df_clean = bp.read_csv(
        dirty_file,
        target_currency=target_currency,
        keep_currency_col=True,  # Adds an audit column showing original currency of each row
    )

    # 5. Save to a NEW file (NEVER overwriting the raw dirty file)
    output_filename = f"clean_sales_{target_currency.lower()}.csv"
    output_path = current_dir / output_filename
    df_clean.to_csv(output_path, index=False)

    # 6. Show AFTER cleaning preview
    print("\n" + "-" * 75)
    print(f"AFTER CLEANING & CONVERSION (Standardized to {target_currency}):")
    preview_cols = ["customer_name_client", "gross_revenue", "gross_revenue_original_currency", "unit_cost", "profit_margin"]
    print(df_clean[preview_cols].head(5).to_string(index=False))
    print("-" * 75)

    # 7. Summary Financial KPIs
    total_rev = df_clean["gross_revenue"].sum()
    total_cost = df_clean["unit_cost"].sum()
    net_profit = total_rev - total_cost
    margin_pct = (net_profit / total_rev) * 100.0

    symbol = bp.currency.CODE_TO_SYMBOL.get(target_currency, f"{target_currency} ")
    print(f"\nFINANCIAL REPORT (in {target_currency}):")
    print(f"  * Total Revenue : {symbol}{total_rev:,.2f}")
    print(f"  * Total Cost    : {symbol}{total_cost:,.2f}")
    print(f"  * Net Profit    : {symbol}{net_profit:,.2f}")
    print(f"  * Profit Margin : {margin_pct:.1f}%")

    # 8. Run 80/20 Pareto analysis
    print(f"\nRunning 80/20 Pareto Analysis on Customers...")
    pareto_df = bp.pareto(df_clean, dim_col="customer_name_client", metric_col="gross_revenue", top_pct=0.80)
    print(f"  * {pareto_df.attrs.get('summary')}")

    print(f"\n[Success] New clean file created at: {output_path.resolve()}")
    print("=" * 75)


if __name__ == "__main__":
    main()
