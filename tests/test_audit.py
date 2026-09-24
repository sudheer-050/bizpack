import pytest
import pandas as pd
import numpy as np
import bizpack as bp
from bizpack.audit import audit, AuditReport


def test_audit_clean_dataframe():
    clean_data = pd.DataFrame({
        "account_id": [1, 2, 3],
        "revenue": [100.0, 200.0, 300.0],
        "is_active": [True, False, True],
    })
    report = bp.audit(clean_data, print_report=False)
    assert isinstance(report, AuditReport)
    assert report.score >= 90
    assert report.rating == "EXCELLENT"
    assert len(report.issues) == 0


def test_audit_detects_multi_currency_conflict():
    dirty_data = pd.DataFrame({
        "revenue": ["$ 100.00", "₹ 8,900.00", "€ 100.00"],
    })
    report = bp.audit(dirty_data, print_report=False)
    assert report.score < 90
    severities = [issue["severity"] for issue in report.issues]
    assert "HIGH" in severities
    assert any("Multi-currency" in issue["message"] for issue in report.issues)


def test_audit_detects_leading_zero_id_risk():
    id_data = pd.DataFrame({
        "zip_code": ["00124", "07001", "00042"],
    })
    report = bp.audit(id_data, print_report=False)
    assert any("leading zeros" in issue["message"] for issue in report.issues)


def test_audit_detects_footer_totals():
    sheet_data = pd.DataFrame({
        "customer": ["Acme Corp", "Wayne Ent", "Grand Total"],
        "sales": [100, 200, 300],
    })
    report = bp.audit(sheet_data, print_report=False)
    assert any("Grand Total" in issue["message"] for issue in report.issues)


def test_audit_detects_empty_columns():
    empty_data = pd.DataFrame({
        "id": [1, 2, 3],
        "blank_col": [np.nan, np.nan, np.nan],
    })
    report = bp.audit(empty_data, print_report=False)
    assert any("empty" in issue["message"] for issue in report.issues)


def test_audit_accessor():
    df = pd.DataFrame({"sales": ["$100", "($50)"]})
    report = df.biz.audit(print_report=False)
    assert isinstance(report, AuditReport)
    rep_dict = report.to_dict()
    assert "score" in rep_dict
    assert "rating" in rep_dict
    assert "issues" in rep_dict
    assert str(report) != ""
