"""
Data Health Audit and Diagnostic Scorecard for BizPack.
Evaluates spreadsheets for multi-currency conflation, date format ambiguities,
ID truncation risks, accounting deficits, and structural defects.
"""

from typing import Dict, List, Any, Optional
import re
import pandas as pd
import numpy as np

from bizpack.currency import detect_currency


class AuditReport:
    """Represents the results of a BizPack Data Health Audit."""

    def __init__(
        self,
        score: int,
        rating: str,
        issues: List[Dict[str, Any]],
        stats: Dict[str, Any],
        recommendation: str,
    ):
        self.score = score
        self.rating = rating
        self.issues = issues
        self.stats = stats
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to standard dictionary."""
        return {
            "score": self.score,
            "rating": self.rating,
            "issues": self.issues,
            "stats": self.stats,
            "recommendation": self.recommendation,
        }

    def __repr__(self) -> str:
        return f"<BizPack AuditReport: score={self.score}/100 rating='{self.rating}' issues={len(self.issues)}>"

    def __str__(self) -> str:
        border = "=" * 66
        sub_border = "-" * 66
        lines = [
            border,
            "                 BIZPACK DATA HEALTH AUDIT SCORECARD",
            border,
            f" Overall Health Score: {self.score} / 100  [{self.rating}]",
            f" Records Analyzed:     {self.stats.get('rows', 0)} rows | {self.stats.get('cols', 0)} columns",
            f" Data Completeness:    {self.stats.get('completeness_pct', 100):.1f}%",
            sub_border,
        ]

        if not self.issues:
            lines.append(" [*] No major spreadsheet defects detected. Dataset is clean.")
        else:
            lines.append(" ISSUES DETECTED:")
            for issue in self.issues:
                sev_icon = "[!] [HIGH] " if issue["severity"] == "HIGH" else "[!] [WARN] " if issue["severity"] == "MEDIUM" else "[i] [INFO] "
                lines.append(f" {sev_icon} {issue['column']}: {issue['message']}")

        lines.extend([
            sub_border,
            f" RECOMMENDATION: {self.recommendation}",
            border,
        ])
        return "\n".join(lines)


def audit(df: pd.DataFrame, print_report: bool = True) -> AuditReport:
    """
    Performs a non-destructive data health audit on a DataFrame.

    Checks for:
    1. Multi-currency conflation risks (e.g. mixed $, €, ₹ in 1 column).
    2. Date format ambiguity (mixed DD/MM and MM/DD conventions).
    3. Accounting parentheses deficits (e.g. '($1,200)' turning positive).
    4. Account ID & ZIP code leading zero truncation risks ('00124').
    5. Spreadsheet footer leakage ('Grand Total' rows).
    6. Blank rows, empty columns, and spreadsheet error strings (#REF!, #N/A).
    7. Dirty column titles (whitespace, slashes, special characters).

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to inspect.
    print_report : bool, default True
        Whether to print the formatted scorecard to stdout.

    Returns
    -------
    AuditReport
        A structured report object containing score, rating, and issues list.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")

    score = 100
    issues: List[Dict[str, Any]] = []
    rows, cols = df.shape

    # 1. Check Empty Rows / Columns
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        score -= min(15, len(empty_cols) * 5)
        issues.append({
            "severity": "MEDIUM",
            "column": f"Columns {empty_cols}",
            "message": f"{len(empty_cols)} column(s) are 100% empty and should be dropped.",
        })

    empty_rows_count = int(df.isna().all(axis=1).sum())
    if empty_rows_count > 0:
        score -= min(10, empty_rows_count * 2)
        issues.append({
            "severity": "MEDIUM",
            "column": "Entire Sheet",
            "message": f"{empty_rows_count} row(s) are completely empty.",
        })

    # 2. Check Dirty Column Names
    dirty_headers = []
    for c in df.columns:
        c_str = str(c)
        if c_str != c_str.strip() or re.search(r"[\s/#%()\-]+", c_str) or any(char.isupper() for char in c_str):
            dirty_headers.append(c_str)
    if dirty_headers:
        score -= 10
        issues.append({
            "severity": "LOW",
            "column": "Headers",
            "message": f"{len(dirty_headers)} column title(s) contain spaces, uppercase, or special characters.",
        })

    # 3. Check for Footer / Total Rows
    total_keywords = ["grand total", "total", "subtotal", "summary", "totals"]
    tail_rows = min(5, rows)
    tail_df = df.tail(tail_rows)
    found_footer = False
    for idx, row in tail_df.iterrows():
        first_non_null = row.dropna()
        if not first_non_null.empty:
            val_str = str(first_non_null.iloc[0]).strip().lower()
            if any(val_str == kw or val_str.startswith(kw) for kw in total_keywords):
                found_footer = True
                break
    if found_footer:
        score -= 15
        issues.append({
            "severity": "HIGH",
            "column": "Footer",
            "message": "Detected 'Grand Total' or summary row at bottom of sheet (risk of 2x revenue inflation).",
        })

    # 4. Column-by-column inspection
    for col in df.columns:
        s = df[col]
        non_nulls = s.dropna().astype(str).str.strip()
        if non_nulls.empty:
            continue

        # A. Currency Conflation & Symbols
        curr_symbols = set()
        for v in non_nulls:
            c = detect_currency(v)
            if c:
                curr_symbols.add(c)

        if len(curr_symbols) > 1:
            score -= 20
            issues.append({
                "severity": "HIGH",
                "column": str(col),
                "message": f"Multi-currency conflict detected: {sorted(list(curr_symbols))}. Summing will cause massive financial errors!",
            })
        elif len(curr_symbols) == 1:
            # Check accounting parentheses: ($1,200) or (1,200)
            has_acct = non_nulls.str.contains(r"\([\d,.]+\)", regex=True).any()
            if has_acct:
                score -= 10
                issues.append({
                    "severity": "MEDIUM",
                    "column": str(col),
                    "message": "Accounting parentheses deficits detected (e.g. '($1,200)'). Naive regex will convert losses into profits.",
                })

        # B. ID Columns with Leading Zeros
        has_leading_zeros = non_nulls.str.match(r"^0\d+$").any()
        if has_leading_zeros:
            score -= 10
            issues.append({
                "severity": "HIGH",
                "column": str(col),
                "message": "Values with leading zeros detected (e.g. '00124'). High risk of integer truncation in standard Pandas.",
            })

        # C. Date Ambiguity
        date_pattern = r"^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$"
        date_matches = non_nulls.str.match(date_pattern)
        if date_matches.mean() > 0.5:
            # Check if ambiguous between DD/MM and MM/DD
            parts = non_nulls[date_matches].str.split(r"[/\-\.]", expand=True)
            if parts.shape[1] >= 2:
                try:
                    p0 = pd.to_numeric(parts[0], errors="coerce")
                    p1 = pd.to_numeric(parts[1], errors="coerce")
                    has_p0_gt_12 = (p0 > 12).any()
                    has_p1_gt_12 = (p1 > 12).any()
                    if has_p0_gt_12 and has_p1_gt_12:
                        score -= 20
                        issues.append({
                            "severity": "HIGH",
                            "column": str(col),
                            "message": "Contradictory dates in same column (both DD/MM and MM/DD found). pd.to_datetime will fail or flip months.",
                        })
                    elif not has_p0_gt_12 and not has_p1_gt_12:
                        score -= 10
                        issues.append({
                            "severity": "MEDIUM",
                            "column": str(col),
                            "message": "Ambiguous dates (all day/month <= 12). High risk of silent month/day inversion.",
                        })
                except Exception:
                    pass

        # D. Spreadsheet Error Strings (#REF!, #N/A, null, -)
        error_strings = {"#ref!", "#n/a", "#value!", "#div/0!", "null", "none", "-"}
        err_matches = non_nulls.str.lower().isin(error_strings)
        err_count = int(err_matches.sum())
        if err_count > 0:
            score -= 5
            issues.append({
                "severity": "LOW",
                "column": str(col),
                "message": f"Contains {err_count} spreadsheet error string(s) (e.g. '#REF!', 'null', '-').",
            })

    # Clamp score between 0 and 100
    score = max(0, min(100, score))

    if score >= 90:
        rating = "EXCELLENT"
        recommendation = "Dataset is clean and ready for analysis."
    elif score >= 75:
        rating = "GOOD"
        recommendation = "Dataset has minor defects. Run `bp.clean(df)` for best results."
    elif score >= 50:
        rating = "NEEDS CLEANING"
        recommendation = "Run `clean_df = bp.clean(df)` to resolve currency, date, or formatting conflicts."
    else:
        rating = "CRITICAL"
        recommendation = "Severe financial / structural defects detected. Immediate `bp.clean()` required before any math."

    total_cells = rows * cols if (rows * cols) > 0 else 1
    null_cells = int(df.isna().sum().sum())
    completeness = ((total_cells - null_cells) / total_cells) * 100.0

    stats = {
        "rows": rows,
        "cols": cols,
        "completeness_pct": completeness,
        "issues_count": len(issues),
    }

    report = AuditReport(
        score=score,
        rating=rating,
        issues=issues,
        stats=stats,
        recommendation=recommendation,
    )

    if print_report:
        try:
            print(str(report))
        except UnicodeEncodeError:
            print(str(report).encode("ascii", errors="replace").decode("ascii"))

    return report
