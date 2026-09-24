"""
Quickstart example demonstrating BizKit:
1. One-line cleaning of dirty business data
2. Intuitive business formulas (XLOOKUP, Pareto, MoM Growth, Pacing)
3. Restoring executive presentation formatting
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import bizkit as bk

print("=" * 70)
print("1. LOADING MESSY BUSINESS DATA (TYPICAL SPREADSHEET EXPORT)")
print("=" * 70)

raw_data = {
    " Customer Name / Account ": ["Acme Corp", "Globex Inc", "Initech LLC", "Umbrella Corp", "Wayne Ent", "Grand Total"],
    " Revenue ($) ": ["$125,000.50", "($14,200.00)", "$85,400.00", "$450,000", "$920,000.00", "$1,566,200.50"],
    " Margin % ": ["22.5%", "(3.1%)", "18.0%", "35.2%", "40.0%", "28.5%"],
    " Order Date ": ["2024-03-01", "2024-03-05", "2024-03-12", "2024-03-18", "2024-03-25", "-"],
    " Account_ID ": ["00101", "00102", "00103", "00104", "00105", "N/A"],
    " Active? ": ["Y", "N", "Yes", "Y", "Yes", ""]
}
df = pd.DataFrame(raw_data)
print("\nRaw Dirty DataFrame:")
print(df)
print("\nRaw Data Types:")
print(df.dtypes)

print("\n" + "=" * 70)
print("2. ONE-LINE MAGIC CLEANING (bk.clean)")
print("=" * 70)

clean_df = bk.clean(df)
print("\nCleaned DataFrame:")
print(clean_df)
print("\nCleaned Data Types (Auto-converted):")
print(clean_df.dtypes)
print("\nPreserved Footer Summary in df.attrs['totals']:")
print(clean_df.attrs.get("totals"))

print("\n" + "=" * 70)
print("3. INTUITIVE BUSINESS FORMULAS")
print("=" * 70)

# A. Pareto 80/20 Analysis
pareto_df = bk.pareto(clean_df, dim_col="customer_name_account", metric_col="revenue")
print("\nPareto (80/20 Rule) Analysis:")
print(pareto_df[["customer_name_account", "revenue", "cumulative_share", "is_top_80"]])
print(f"\n[Insight] {pareto_df.attrs['summary']}")

# B. Pythonic XLOOKUP
# Let's say we have a lookup catalog of tiers:
tiers_catalog = pd.DataFrame({
    "acct": ["00101", "00104", "00105"],
    "tier": ["Silver", "Enterprise", "Enterprise Platinum"]
})
clean_df["service_tier"] = bk.xlookup(
    clean_df["account_id"],
    tiers_catalog["acct"],
    tiers_catalog["tier"],
    default="Standard"
)
print("\nAfter XLOOKUP (Added 'service_tier' without df.merge boilerplate):")
print(clean_df[["customer_name_account", "account_id", "service_tier"]])

# C. Pacing & Run-rate towards target
run_rate_df = bk.run_rate(
    clean_df,
    date_col="order_date",
    metric_col="revenue",
    target=2_000_000,
    period="M"
)
print("\nMonth-to-Date Pacing & Projected Run-Rate:")
print(run_rate_df.T)

print("\n" + "=" * 70)
print("4. EXECUTIVE PRESENTATION FORMATTING (bk.format_for_display)")
print("=" * 70)

# Calculate profit
clean_df["profit"] = clean_df["revenue"] * clean_df["margin"]

# Turn clean numbers back into $, %, and accounting () for presentation
display_df = bk.format_for_display(clean_df)
# Also format our newly calculated profit column as accounting
display_df["profit"] = bk.format_accounting(clean_df["profit"])

print("\nFinal Boardroom-Ready Table:")
print(display_df[["customer_name_account", "account_id", "revenue", "margin", "profit", "service_tier"]])
