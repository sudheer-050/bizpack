# BizPack

**The Python toolkit for business & data analysts.**  
*Zero-friction spreadsheet cleaning + intuitive business formulas without drowning in Pandas boilerplate.*

---

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/bizpack/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-29%20passed-brightgreen.svg)]()
[![Core Dependencies](https://img.shields.io/badge/core%20deps-pandas%20%2B%20numpy-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## Why BizPack?

Pandas is built for general data science and software engineering. For everyday business and financial analysis, it is notoriously verbose:
* Doing a simple **XLOOKUP** takes a 4-line `df.merge()` with temporary join keys.
* Calculating a **Month-over-Month (MoM) growth rate** requires manual `.shift(1)` and delta math.
* Cleaning dirty spreadsheet exports (`$1,250.00`, `(450.00)`, `15.4%`, `"Grand Total"` footers) requires copy-pasting **20+ lines of brittle regex**.
* **Mixed Currency Disaster:** If a column mixes US Dollars (`$100`), Euros (`€100`), and Indian Rupees (`₹8,900`), naive cleaning strips the symbols and sums `100 + 100 + 8900 = 9100`—creating a catastrophic financial error.

**BizPack solves this with three simple layers:**

```text
 Breath 1: INGEST & CLEAN      df = bp.clean(df, target_currency="USD")
                               -> Auto-converts currencies, accounting '()', %, dates, headers, footers
                               -> Standardizes mixed currencies (USD, INR, EUR, GBP) into 1 chosen currency

 Breath 2: BUSINESS FORMULAS   bp.xlookup() . bp.pareto() . bp.growth() . bp.run_rate()
                               -> Vectorized business math without Pandas boilerplate

 Breath 3: PRESENT & EXPORT    display_df = bp.format_for_display(df)
                               -> Turns clean floats back into boardroom-ready $, ₹, €, %, and () strings
```

---

## The Comparison: Before vs. After

| Everyday Task | The Old Way (Pandas Boilerplate) | With BizPack |
| :--- | :--- | :--- |
| **Clean Headers & Dirty Types** | 20+ lines of `.replace()`, regex, `pd.to_numeric` | `df = bp.clean(df)` |
| **Lookup a Value** | 4-line `df.merge()` + `.drop()` + `.fillna()` | `df['cost'] = bp.xlookup(df['id'], cat['sku'], cat['cost'])` |
| **MoM / YoY Growth** | 5 lines of `.groupby()`, `.shift(1)`, and deltas | `growth = bp.growth(df, 'order_date', 'revenue')` |
| **Pareto (80/20 Rule)** | 5 lines of `.sort_values()`, `.cumsum()`, `%` | `pareto = bp.pareto(df, 'customer', 'sales')` |
| **Pacing & Run-rate** | 8 lines of date math and target ratios | `pacing = bp.run_rate(df, 'order_date', 'revenue', target=100k)` |
| **Executive Formatting** | Awkward `lambda x: f"${x:,.2f}"` across columns | `display_df = bp.format_for_display(df)` |

---

## Installation

```bash
pip install bizpack
```

*Requirements: Python >= 3.9, pandas, numpy (Zero heavy dependencies).*

---

## Quickstart

### 1. One-Line Data Cleaning
Takes a raw, messy spreadsheet export and makes it analysis-ready:

```python
import pandas as pd
import bizpack as bp

df = pd.read_csv("messy_sales_report.csv")

# 1 line cleans headers, currencies, accounting negatives, and drops footers
clean_df = bp.clean(df)
```

**What it automatically handles:**
* **Headers:** `" Customer Name / Account "` $\rightarrow$ `"customer_name_account"`
* **Currencies:** `"$125,000.50"` $\rightarrow$ `125000.5` (`float64`)
* **Accounting Negatives:** `"(14,200.00)"` or `"$ (14,200)"` $\rightarrow$ `-14200.0` (`float64`)
* **Percentages:** `"22.5%"` $\rightarrow$ `0.225` (`float64`)
* **Sheet Footers:** Detects and strips `"Grand Total"` rows (saved in `df.attrs['totals']`)
* **ID Protection:** Recognizes leading zeros (`"00101"`, `"07001"`) and prevents numeric corruption

---

### 2. Multi-Currency Standardization & Conversion

Multinational business reports frequently contain mixed currencies in the same column (e.g. `$100`, `₹8,900`, `€100`, `£50`). Simply stripping the symbols produces financially invalid numbers.

BizPack automatically detects mixed currencies, prompts the user interactively (or takes `target_currency`), and converts all values using real-world exchange rates:

```python
# Standardize all currency columns to Indian Rupees (INR)
clean_df = bp.clean(df, target_currency="INR")

# Standardize to US Dollars (USD) and keep audit column
clean_df = bp.read_csv("dirty_sales.csv", target_currency="USD", keep_currency_col=True)

# Interactive mode: if target_currency is not set and mixed currencies exist,
# BizPack asks the analyst directly in the terminal:
# [BizPack Alert] Multiple currencies detected in column 'gross_revenue': [EUR, GBP, INR, USD]
# Which currency would you like to standardize to? [USD]:
```

**Custom Exchange Rates:**
```python
# Provide custom FX rates relative to USD
clean_df = bp.clean(df, target_currency="INR", rates={"INR": 1.0 / 90.0, "EUR": 1.10})
```

**Audit Trail:**
BizPack records full transparency in `clean_df.attrs['currency_conversions']`, logging original currencies found, rates used, and row counts converted.

---

### 3. Intuitive Business Formulas

#### Pythonic XLOOKUP
No more awkward `df.merge()` key management:
```python
df["tier"] = bp.xlookup(
    lookup_val=df["account_id"],
    lookup_series=catalog["sku"],
    return_series=catalog["tier_name"],
    default="Standard"
)
```

#### Pareto (80/20 Rule) Analysis
Instantly find which top accounts drive 80% of your revenue:
```python
pareto_df = bp.pareto(clean_df, dim_col="customer_name", metric_col="revenue", top_pct=0.80)

print(pareto_df.attrs["summary"])
# Output: "Top 14 out of 100 customer_name items (14.0%) account for 80% of total revenue."
```

#### Period-over-Period Growth (MoM, YoY)
Calculates dollar delta and percentage growth with zero date headache:
```python
growth_df = bp.growth(clean_df, date_col="order_date", metric_col="revenue", freq="M")
```

#### Business Pacing & Run-rate
Find out whether you are on track to hit your monthly/quarterly target:
```python
run_rate_df = bp.run_rate(
    clean_df, 
    date_col="order_date", 
    metric_col="revenue", 
    target=2_000_000, 
    period="M"
)
```

---

### 4. Executive Presentation Formatting

When doing math, computers need floats. When presenting to stakeholders, executives need `$`, `₹`, `€`, and `%`. 

BizPack remembers original column formats and restores them in **one line**:

```python
# Do your calculations
clean_df["profit"] = clean_df["revenue"] * clean_df["margin"]

# Turn clean floats back into $, ₹, %, and () strings for presentation
display_df = bp.format_for_display(clean_df)
```

---

### 5. Seamless Pandas Accessor

You can also use BizPack directly as a native Pandas accessor:

```python
import bizpack  # registers .biz accessor

clean_df = df.biz.clean()
pareto_df = clean_df.biz.pareto(dim_col="region", metric_col="sales")
display_df = clean_df.biz.format()
```

---

## Architecture

```text
bizpack/
├── cleaner.py          # Auto-clean headers, types, accounting '()', footers
├── currency.py         # Multi-currency detection, conversion, exchange rates & user prompt
├── formulas.py         # Business math: xlookup, pareto, growth, run_rate
├── formatters.py       # Presentation formatters: format_currency, format_percent, format_for_display
├── accessor.py         # Native df.biz.* DataFrame accessor
└── __init__.py         # Public API
```

---

## Running Tests

BizPack is thoroughly tested against messy real-world spreadsheet edge cases:

```bash
git clone https://github.com/sudheer-050/bizpack.git
cd bizpack
python -m pytest tests/ -v
```

---

## Contributing & Roadmap

We welcome contributions! Please feel free to submit issues or pull requests.
* [ ] Multi-table sheet dissector
* [ ] Waterfall variance decomposition
* [ ] Excel formatting exporter (.xlsx with styled headers and native cell formats)

## License

MIT License. See [LICENSE](LICENSE) for details.
