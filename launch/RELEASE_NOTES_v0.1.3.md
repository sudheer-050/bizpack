# BizPack v0.1.3: Silent-Failure Hardening Release

This release closes a batch of edge cases found during an intensive round of
independent stress-testing (four separately constructed "dirty" datasets,
each targeting a different class of real-world spreadsheet mess). No public
API changes — pure correctness and transparency fixes.

### 🐛 Fixed

- **Pareto (80/20) negative-value distortion:** `bp.pareto()` now ranks and
  accumulates by absolute magnitude, so refund/return rows (negative values)
  no longer produce a non-monotonic or misleading `cumulative_share`.
- **Date engine ignored row context on ISO-dominated columns:** columns where
  most dates were ISO (`YYYY-MM-DD`) now still consult row-level partner
  context (currency symbol / country) for the remaining ambiguous slash-dates
  in the same column, instead of guessing a single global convention.
- **Currency codes glued to digits went undetected:** values like `"EUR900"`
  (no space between the ISO code and the amount) are now correctly detected
  as currency.
- **Mixed `1`/`0` boolean tokens weren't recognized** alongside `yes/no`,
  `true/false`, `y/n` — a column using `1`/`0` mixed with those tokens now
  converts to boolean instead of being left as text.
- **Silent unparseable currency/number values:** a value that can't be parsed
  (e.g. an unrecognized currency code) used to become `NaN` with zero record
  of what happened. It's now tracked in `df.attrs` and surfaced as a
  `bp.audit()` warning, with sample offending values included.
- **Whole currency columns silently bypassed:** if a handful of values in an
  otherwise-clean currency column failed to parse (e.g. a symbol variant
  written without diacritics), the *entire column* used to be left completely
  raw and unconverted with no explanation. It now converts the parseable
  majority and flags the rest, consistent with the point above.
- **`bp.format_for_display()` mis-formatted percentages on columns containing
  a value over 100%** (e.g. `1.50` for "150%") — it was guessing ratio-vs-
  whole-percent from the data's value range, which breaks on legitimate ratio
  columns with an outlier. It now uses the exact mode recorded during
  `bp.clean()`.

### ✅ Verification

- 43/43 unit tests passing.
- Re-verified against four independently constructed synthetic dirty
  datasets covering currency, date, boolean, large-integer-ID precision, and
  percentage edge cases, with every value hand-checked against expected
  results.

### 📦 PyPI

https://pypi.org/project/bizpack/0.1.3/
