import sys
from pathlib import Path
import pandas as pd
import bizpack as bp

# Windows UTF-8 console support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)

csv_file = Path(__file__).parent / "dirty_data.csv"

# 1. Before cleaning
print("--- BEFORE CLEANING ---")
print(pd.read_csv(csv_file).head(6))

# 2. Clean directly in 1 line
clean_df = bp.read_csv(csv_file, target_currency="INR")

# 3. After cleaning
print("\n--- AFTER CLEANING ---")
print(clean_df.head(6))
