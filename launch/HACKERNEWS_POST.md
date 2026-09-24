# 🟧 Hacker News (Show HN) Post for BizPack

**Target Site:** https://news.ycombinator.com/submit
**Best Timing:** Tuesday or Wednesday, 8:00 AM – 10:00 AM US Eastern Time

---

## Title:
> **Show HN: BizPack – Clean dirty multi-currency spreadsheets and run Excel math in Python**

---

## URL:
`https://github.com/sudheer-050/bizpack`

---

## Text (Optional comment after submitting):

Hi HN,

I built BizPack because I kept seeing business and finance analysts struggle with Pandas when working with real-world corporate spreadsheets.

While Pandas is great for ML and stats, everyday spreadsheet exports have subtle traps:
- Mixed currencies in one column ($100, €100, ₹8,900) where stripping symbols naively sums `100+100+8900 = 9100` instead of converting using FX rates.
- Ambiguous dates where `05/09/2024` from an Indian subsidiary is Sept 5th, while `05/09/2024` from the US subsidiary is May 9th. `pd.to_datetime` usually applies a single global guess or drops rows to `NaT`.
- Accounting brackets `($1,200.00)` turning into positive `+1200` with standard regex.
- Account numbers with leading zeros (`"00124"`) getting truncated to integers (`124`).
- Doing a simple XLOOKUP requires a 4-line merge with temporary join keys.

BizPack solves this in 1 line:
```python
import bizpack as bp
clean_df = bp.clean_file("dirty_data.csv", "clean_data.csv")
```

It includes:
1. An interactive terminal prompt (or parameter) to standardize mixed currencies with real exchange rates and an audit log in `df.attrs`.
2. A two-tier date engine that uses column consensus first, and falls back to row-level partner columns (currency symbol or country name) to disambiguate dates with 0 dropped rows.
3. Native vectorized business math: `bp.xlookup()`, `bp.pareto()` (80/20 distribution with auto-narrative summary), `bp.growth()` (MoM/YoY), and `bp.run_rate()` (quota pacing).
4. Boardroom formatter to convert clean floats back into executive presentation strings (`$`, `₹`, `%`, `()`).

Zero heavy dependencies (pure Pandas + NumPy).

GitHub: https://github.com/sudheer-050/bizpack
PyPI: `pip install bizpack`

I'd appreciate any feedback on the design decisions or edge cases you've run into!
