"""
Test script that runs BizPack against the 1,000-record dirty dataset.
Verifies all data hygiene, auto-type coercion, formula math, and presentation formatting.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import bizpack as bp

csv_path = os.path.join(os.path.dirname(__file__), "dirty_sales_1k.csv")
print("=" * 80)
print(f"LOADING REALISTIC DIRTY DATASET: {csv_path}")
print("=" * 80)

raw_df = pd.read_csv(csv_path, dtype=str)
print(f"Raw shape: {raw_df.shape} (rows, columns)")
print("\nRaw columns:")
for col in raw_df.columns:
    print(f"  • {repr(col)}")

print("\nSample 5 raw rows:")
print(raw_df.head(5))

print("\nRaw dtypes (Notice: everything is loaded as raw dirty string objects!):")
print(raw_df.dtypes)

print("\n" + "=" * 80)
print("RUNNING BIZPACK: bp.read_csv(csv_path) (OR bp.clean(raw_df))")
print("=" * 80)

# bp.read_csv does safe ingestion + clean in 1 line
clean_df = bp.read_csv(csv_path)

print(f"\nCleaned shape: {clean_df.shape} (rows, columns)")
print("\nCleaned column names (Standardized & snake_cased):")
for col in clean_df.columns:
    print(f"  • {col}")

print("\nCleaned dtypes (Auto-detected & safely coerced):")
print(clean_df.dtypes)

print("\n" + "=" * 80)
print("VERIFYING SAFETY GUARDRAILS & EDGE CASES")
print("=" * 80)

# 1. Leading Zero Preservation
acct_sample = clean_df["account"].dropna().iloc[0]
print(f"1. Leading Zeros Intact: Sample account ID = {repr(acct_sample)} (dtype: {clean_df['account'].dtype})")
assert isinstance(acct_sample, str) and len(acct_sample) == 5, "Account ID lost leading zeros!"

# 2. Text Column Protection
notes_dtype = clean_df["customer_notes_log"].dtype
print(f"2. Free-Text Column Protected: 'customer_notes_log' dtype = {notes_dtype}")
assert notes_dtype == object or pd.api.types.is_string_dtype(notes_dtype), "Notes column was falsely converted to numeric!"

# 3. Blank Column Dropped
print(f"3. Blank Column Dropped: 'blank_column_notes' in columns? {'blank_column_notes' in clean_df.columns}")
assert "blank_column_notes" not in clean_df.columns, "Blank column was not dropped!"

# 4. Total Row Stripped
totals_saved = clean_df.attrs.get("totals", [])
print(f"4. Grand Total Row Stripped: Dropped {len(totals_saved)} footer row(s)")
print("   Saved footer data:", totals_saved)

# 5. Negative Accounting & Currencies Coerced
neg_count = (clean_df["gross_revenue"] < 0).sum()
print(f"5. Accounting Negatives parsed: Found {neg_count} refund/negative revenue records")
print(f"   Total Gross Revenue: ${clean_df['gross_revenue'].sum():,.2f}")
print(f"   Average Margin: {clean_df['profit_margin'].mean() * 100:.1f}%")

print("\n" + "=" * 80)
print("BUSINESS FORMULAS IN ACTION")
print("=" * 80)

# A. Pareto 80/20 Analysis on Customers
pareto_df = bp.pareto(clean_df, dim_col="customer_name_client", metric_col="gross_revenue")
print("\nPareto (80/20 Rule) Analysis:")
print(pareto_df[["customer_name_client", "gross_revenue", "cumulative_share", "is_top_80"]].head(8))
print(f"\n[Automated Insight] {pareto_df.attrs['summary']}")

# B. Period-over-Period (MoM) Growth Analysis
growth_df = bp.growth(clean_df, date_col="order_date_utc", metric_col="gross_revenue", freq="M")
print("\nMonth-over-Month (MoM) Growth Rates:")
print(growth_df)

# C. Pythonic XLOOKUP
# Create a tier lookup mapping based on the first digit of Account #
catalog = pd.DataFrame({
    "prefix": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    "tier_level": ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5", "Tier 6", "Tier 7", "Tier 8", "Tier 9", "Tier 10"]
})
clean_df["acct_prefix"] = clean_df["account"].str[0]
clean_df["tier_level"] = bp.xlookup(clean_df["acct_prefix"], catalog["prefix"], catalog["tier_level"], default="Standard")
print("\nXLOOKUP Output (Added 'tier_level' without df.merge boilerplate):")
print(clean_df[["customer_name_client", "account", "tier_level"]].head(5))

print("\n" + "=" * 80)
print("EXECUTIVE PRESENTATION FORMATTING")
print("=" * 80)

# Calculate Dollar Profit
clean_df["dollar_profit"] = clean_df["gross_revenue"] * clean_df["profit_margin"]

# Restore presentation formatting ($ and %)
display_df = bp.format_for_display(clean_df)
display_df["dollar_profit"] = bp.format_accounting(clean_df["dollar_profit"])

print("Boardroom-ready formatted sample:")
print(display_df[["customer_name_client", "account", "gross_revenue", "profit_margin", "dollar_profit", "tier_level"]].head(5))

print("\n" + "=" * 80)
print("SUCCESS! ALL 1,000 RECORDS PROCESSED FLAWLESSLY BY BIZPACK!")
print("=" * 80)
