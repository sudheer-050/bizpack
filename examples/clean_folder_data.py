"""
Script to clean the data in this folder using BizPack:
1. Ingests dirty_sales_1k.csv
2. Automatically fixes headers, accounting numbers, currencies, and strips footer rows
3. Saves a clean analysis-ready CSV ('cleaned_sales_1k.csv')
4. Saves an executive formatted Excel report ('cleaned_sales_1k.xlsx')
"""

import os
import pandas as pd
import bizpack as bp

# Target folder
folder = os.path.dirname(os.path.abspath(__file__))
input_csv = os.path.join(folder, "dirty_sales_1k.csv")
output_csv = os.path.join(folder, "cleaned_sales_1k.csv")
output_excel = os.path.join(folder, "cleaned_sales_1k.xlsx")

print("=" * 70)
print(f"1. INGESTING & CLEANING: {input_csv}")
print("=" * 70)

# bp.read_csv automatically handles:
# - Header sanitization & snake_casing
# - Stripping $, €, £, %, and parsing accounting negatives '(1,250.00)' -> -1250.0
# - Stripping 'Grand Total' summary footer rows
# - Dropping empty rows and empty columns
# - Preserving leading zeros in IDs and ZIP codes
clean_df = bp.read_csv(input_csv)

print(f"Done! Cleaned DataFrame shape: {clean_df.shape} (rows, columns)")

print("\n" + "=" * 70)
print("2. SAVING CLEANED OUTPUT FILES")
print("=" * 70)

# Save clean CSV for database/analytics use (with pure numeric floats)
clean_df.to_csv(output_csv, index=False)
print(f" Saved clean analysis CSV -> {output_csv}")

# Save presentation Excel file (with restored $, %, and accounting formatting)
display_df = bp.format_for_display(clean_df)
display_df.to_excel(output_excel, index=False)
print(f" Saved presentation Excel -> {output_excel}")

print("\n" + "=" * 70)
print("3. CLEANED COLUMNS & DATA TYPES")
print("=" * 70)
print(clean_df.dtypes)

print("\nSample 5 Clean Records:")
print(clean_df.head(5))
