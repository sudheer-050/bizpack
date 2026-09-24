"""
Clean Dataset Script using BizPack.
Cleans raw/dirty spreadsheet data, prompts for target currency if multiple currencies exist,
and outputs to a brand new clean CSV without touching or overwriting the original raw file.

Usage:
    python clean_dataset.py
    python clean_dataset.py --currency INR
    python clean_dataset.py --currency USD
    python clean_dataset.py --currency EUR
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import bizpack as bp

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="BizPack Zero-Friction Dataset Cleaner")
    parser.add_argument(
        "--input",
        "-i",
        default="dirty_sales_1k.csv",
        help="Path to dirty CSV file (default: dirty_sales_1k.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Path to write new clean CSV (default: clean_sales_<currency>.csv)",
    )
    parser.add_argument(
        "--currency",
        "-c",
        default=None,
        help="Target currency code to standardize to (e.g. USD, INR, EUR, GBP). If omitted and multiple currencies are detected, BizPack will prompt you.",
    )
    parser.add_argument(
        "--keep-audit",
        action="store_true",
        help="Add an audit column tracking each row's original currency.",
    )

    args = parser.parse_args()

    # Locate input file relative to this script or current working directory
    script_dir = Path(__file__).resolve().parent
    input_path = Path(args.input)
    if not input_path.exists():
        input_path = script_dir / args.input
    if not input_path.exists():
        print(f"Error: Could not find input file '{args.input}'")
        sys.exit(1)

    print("=" * 75)
    print("  BIZPACK AUTOMATED DATASET CLEANING & CURRENCY STANDARDIZATION")
    print("=" * 75)
    print(f"Reading raw dirty input: {input_path.name}")
    print("Zero-friction spreadsheet cleaning running...")

    # Read and clean using BizPack
    # If args.currency is None and multiple currencies exist, BizPack prompts the user
    df_clean = bp.read_csv(
        input_path,
        target_currency=args.currency,
        keep_currency_col=args.keep_audit,
    )

    # Determine final currency used
    currency_meta = df_clean.attrs.get("currency_conversions", {})
    final_currency = "USD"
    for col_audit in currency_meta.values():
        final_currency = col_audit.get("target_currency", "USD")
        break

    # Determine output file path (never overwrite raw dirty file!)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = script_dir / f"clean_sales_{final_currency.lower()}.csv"

    # Save to new clean file
    df_clean.to_csv(output_path, index=False)

    print("\n" + "-" * 75)
    print(f"CLEANING COMPLETE! Successfully created new file:")
    print(f"  -> Output: {output_path}")
    print(f"  -> Total records: {len(df_clean):,} rows")
    print(f"  -> Standardized currency: {final_currency}")
    print("-" * 75)

    # Display currency conversion details
    if currency_meta:
        print("\nCURRENCY AUDIT REPORT:")
        for col, audit in currency_meta.items():
            detected = audit.get("detected_currencies", [])
            rates = audit.get("effective_rates_to_target", {})
            converted = audit.get("rows_converted", 0)
            print(f"  Column '{col}':")
            print(f"    - Original currencies detected : {detected}")
            print(f"    - Rows converted to {final_currency}       : {converted:,} / {len(df_clean):,}")
            print(f"    - Exchange rates applied       : {rates}")

    # Summary Financial KPI calculations
    if "gross_revenue" in df_clean.columns and "unit_cost" in df_clean.columns:
        total_rev = df_clean["gross_revenue"].sum()
        total_cost = df_clean["unit_cost"].sum()
        net_profit = total_rev - total_cost
        avg_margin = (net_profit / total_rev) * 100.0 if total_rev > 0 else 0

        sym = bp.currency.CODE_TO_SYMBOL.get(final_currency, f"{final_currency} ")
        print(f"\nFINANCIAL SUMMARY ({final_currency}):")
        print(f"  Total Revenue : {sym}{total_rev:,.2f}")
        print(f"  Total Cost    : {sym}{total_cost:,.2f}")
        print(f"  Net Profit    : {sym}{net_profit:,.2f}")
        print(f"  Profit Margin : {avg_margin:.1f}%")

    print("\nPREVIEW OF CLEAN DATASET (FIRST 5 ROWS):")
    display_cols = [c for c in ["customer_name_client", "account", "order_date_utc", "region_territory", "gross_revenue", "unit_cost", "profit_margin", "active_subscription"] if c in df_clean.columns]
    print(df_clean[display_cols].head(5).to_string(index=False))
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
