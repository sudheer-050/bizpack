# 🚀 Reddit Post Template for BizPack

**Target Subreddits:**
1. `r/Python` (Use the "Project Showcase" flair or post on Showcase Saturday)
2. `r/dataanalysis`
3. `r/excel` (Excel power users adopting Python)
4. `r/datascience`

---

## Post Title:
> **I built BizPack: A Python library for business analysts to clean dirty spreadsheets and run XLOOKUP without 30 lines of Pandas boilerplate**

---

## Post Body:

Hey r/Python,

Over the past few years, I noticed that almost every business, FP&A, and data analyst has the exact same complaint when transitioning from Excel to Pandas:

**Pandas is incredible for general data science, but it's notoriously painful for everyday business data.**

Here are the silent disasters that kept breaking our scripts:
1. **Multi-Currency Conflation:** If an international sales export has `$100`, `€100`, and `₹8,900`, naive regex strips the symbols and sums `100 + 100 + 8900 = 9100`. In reality, `$100 + $108 + $105 = $314`—a catastrophic financial error.
2. **Day/Month Date Roulette:** When an export mixes Indian/European dates (`05/09/2024` = Sept 5) and US dates (`05/09/2024` = May 9), `pd.to_datetime()` guesses one globally or silently drops rows to `NaT`.
3. **The Accounting Parentheses Trap:** Financial deficits formatted as `($14,200.00)` become positive `+14200.00` if you naively strip non-digits, turning losses into reported profits.
4. **Leading Zero Erasure:** ZIP codes `"00124"` and account numbers `"00007"` get cast to integers `124` and `7`, breaking ERP joins.
5. **The Grand Total Inflation:** Excel exports often have a `"Grand Total"` footer row. Calling `df['revenue'].sum()` downstream silently doubles your revenue.

### What is BizPack?

I built **[BizPack](https://github.com/sudheer-050/bizpack)** (`pip install bizpack`) to solve this in **1 line** with zero heavy dependencies (pure Pandas + NumPy):

```python
import bizpack as bp

# 1 line handles headers, mixed currencies, two-tier dates, footers, and types
clean_df = bp.clean_file("dirty_data.csv", "clean_data.csv")
```

### Key Features:
* 🌍 **Multi-Currency Standardization:** Detects mixed currencies (`₹`, `$`, `€`, `£`, `Rs.`), prompts interactively in the terminal or takes a target currency, and applies real FX rates with a full audit log in `df.attrs['currency_conversions']`.
* 📅 **Two-Tier Date Engine:** First checks column consensus; if ambiguous, it inspects row-level partner signals (like `Region: India` or `₹`) to parse dates accurately with **0% dropped rows**.
* 🔍 **Pythonic Business Formulas:** 
  - `bp.xlookup()`: Vectorized Excel lookup without 4-line merge syntax.
  - `bp.pareto()`: Instant 80/20 rule analysis with auto-generated executive summary text.
  - `bp.growth()`: MoM / YoY period deltas and percentage growth.
  - `bp.run_rate()`: Quota pacing against monthly/quarterly targets.
* 👔 **Boardroom Formatter:** `bp.format_for_display(df)` restores clean floats back into `$`, `₹`, `%`, and `()` strings for executive presentations.
* 🔌 **Pandas Accessor:** Can be used directly as `df.biz.clean()`!

---

### Links & Info:
* **PyPI:** https://pypi.org/project/bizpack/
* **GitHub (Full Showcase & Docs):** https://github.com/sudheer-050/bizpack
* **Installation:** `pip install bizpack`

Would love to hear feedback, feature requests, or edge cases from the community!
