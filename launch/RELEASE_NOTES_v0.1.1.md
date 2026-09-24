## ⚡ BizPack v0.1.1 — The Intelligent Business Data Engine for Python

Transform chaotic, multi-currency corporate spreadsheets into pristine, audit-ready DataFrames in 1 line.

### 🌟 Flagship Features in v0.1.1:
- 🌍 **Multi-Currency Normalization:** Auto-detects mixed currencies (`₹`, `$`, `€`, `£`, `Rs.`), prompts interactively or standardizes to target currency using real exchange rates, and stores full audit trail in `df.attrs['currency_conversions']`.
- 📅 **Two-Tier Hierarchical Date Engine:** Deduces `DD/MM/YYYY` vs `MM/DD/YYYY` using column consensus and row-level partner signals (currency, country) with **0% dropped `NaT` rows**.
- 🧹 **Enterprise Spreadsheet Hygiene:** Strips accounting parentheses `($1,200)` into negative numbers, preserves leading zeros in account/ZIP IDs (`00124`), eliminates empty rows/columns, and extracts `Grand Total` footers.
- 📈 **Pythonic Business Math:** Vectorized implementations of `bp.xlookup()`, `bp.pareto()` (80/20 rule), `bp.growth()` (MoM/YoY), and `bp.run_rate()` (quota pacing).
- 👔 **Boardroom Display Formatter:** Restores clean numerical floats back into executive presentation strings (`$`, `₹`, `%`, `()`).
- 🔌 **Native Pandas Accessor:** Use directly via `df.biz.clean()`, `df.biz.pareto()`, etc.

### 📦 Installation:
```bash
pip install bizpack==0.1.1
```
PyPI: https://pypi.org/project/bizpack/0.1.1/
