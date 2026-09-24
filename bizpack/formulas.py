"""
Intuitive business formula helpers for BizKit.
Vectorized business calculations without awkward Pandas boilerplate.
"""

from typing import Any, List, Optional, Union
import numpy as np
import pandas as pd


def xlookup(
    lookup_val: Union[pd.Series, List[Any], Any],
    lookup_series: pd.Series,
    return_series: pd.Series,
    default: Any = np.nan,
) -> Union[pd.Series, Any]:
    """
    Pythonic equivalent of Excel's XLOOKUP function.
    Eliminates the multi-line boilerplate of df.merge(), temporary join keys, and drop().

    Example:
    >>> df['cost'] = bk.xlookup(df['product_id'], catalog['sku'], catalog['unit_cost'], default=0)
    """
    # Create a mapping series
    # Drop duplicates in lookup_series to mimic XLOOKUP's first-match behavior
    mask = ~lookup_series.duplicated(keep="first")
    keys = lookup_series[mask]
    vals = return_series[mask]
    mapping = pd.Series(vals.values, index=keys.values)

    if isinstance(lookup_val, pd.Series):
        res = lookup_val.map(mapping)
        if default is not None and not (isinstance(default, float) and np.isnan(default)):
            res = res.fillna(default)
        return res
    elif isinstance(lookup_val, (list, tuple, np.ndarray)):
        s = pd.Series(lookup_val)
        res = s.map(mapping)
        if default is not None and not (isinstance(default, float) and np.isnan(default)):
            res = res.fillna(default)
        return res.tolist()
    else:
        # Scalar lookup
        val = mapping.get(lookup_val, default)
        return val if val is not None else default


def growth(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    freq: str = "M",
    group_by: Optional[Union[str, List[str]]] = None,
) -> pd.DataFrame:
    """
    Compute Period-over-Period (MoM, YoY, QoQ) growth with zero date headache.

    Parameters:
    - df: Input DataFrame
    - date_col: Name of datetime or date string column
    - metric_col: Numeric column to aggregate and measure growth
    - freq: Period frequency ('D' for daily, 'W' for weekly, 'M' for monthly, 'Q' for quarterly, 'Y' for yearly)
    - group_by: Optional column(s) to segment growth by (e.g. 'region' or 'product_tier')

    Returns:
    DataFrame with period, current metric, prior metric, dollar change, and percentage growth.
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # Drop invalid dates or metrics
    df = df.dropna(subset=[date_col, metric_col])

    # Convert date to period string
    freq_clean = freq.upper()
    df["_period"] = df[date_col].dt.to_period(freq_clean)

    group_cols = []
    if group_by:
        group_cols = [group_by] if isinstance(group_by, str) else list(group_by)

    agg_cols = group_cols + ["_period"]
    summary = df.groupby(agg_cols, as_index=False)[metric_col].sum()
    summary = summary.sort_values(by=agg_cols).reset_index(drop=True)

    if group_cols:
        summary["prior_" + metric_col] = summary.groupby(group_cols)[metric_col].shift(1)
    else:
        summary["prior_" + metric_col] = summary[metric_col].shift(1)

    summary["delta_" + metric_col] = summary[metric_col] - summary["prior_" + metric_col]
    
    # Calculate percentage growth safely
    with np.errstate(divide="ignore", invalid="ignore"):
        pct = (summary["delta_" + metric_col] / summary["prior_" + metric_col].abs()) * 100.0
        summary["growth_pct"] = np.where(summary["prior_" + metric_col].isna(), np.nan, pct)

    # Rename current metric column
    summary = summary.rename(columns={"_period": "period", metric_col: "current_" + metric_col})
    summary["period"] = summary["period"].astype(str)

    return summary


def pareto(
    df: pd.DataFrame,
    dim_col: str,
    metric_col: str,
    top_pct: float = 0.80,
) -> pd.DataFrame:
    """
    Perform 80/20 Pareto Analysis on any business dimension.
    Ranks segments by contribution, calculates cumulative totals, and flags the top drivers.

    Example:
    >>> pareto_df = bk.pareto(df, dim_col='customer_name', metric_col='revenue')
    """
    df = df.copy()
    summary = df.groupby(dim_col, as_index=False)[metric_col].sum()
    summary = summary.sort_values(by=metric_col, ascending=False).reset_index(drop=True)

    total_sum = summary[metric_col].sum()
    if total_sum <= 0:
        summary["cumulative_" + metric_col] = summary[metric_col].cumsum()
        summary["cumulative_share"] = 0.0
        summary[f"is_top_{int(top_pct * 100)}"] = False
        return summary

    summary["cumulative_" + metric_col] = summary[metric_col].cumsum()
    summary["cumulative_share"] = summary["cumulative_" + metric_col] / total_sum

    # Flag top drivers
    # The item that crosses the threshold is included in top drivers
    is_top = (summary["cumulative_share"].shift(1).fillna(0) < top_pct)
    summary[f"is_top_{int(top_pct * 100)}"] = is_top

    # Store insights in attrs
    top_count = int(is_top.sum())
    total_count = len(summary)
    pct_dim = (top_count / total_count * 100.0) if total_count > 0 else 0
    summary.attrs["summary"] = (
        f"Top {top_count} out of {total_count} {dim_col} items ({pct_dim:.1f}%) "
        f"account for {int(top_pct * 100)}% of total {metric_col}."
    )

    return summary


def run_rate(
    df: pd.DataFrame,
    date_col: str,
    metric_col: str,
    target: Optional[float] = None,
    period: str = "M",
    as_of_date: Optional[Union[str, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """
    Calculate business pacing and projected end-of-period run-rate.

    Parameters:
    - df: Input transactions/revenue DataFrame
    - date_col: Timestamp column
    - metric_col: Revenue or volume column
    - target: Optional dollar or volume quota to evaluate pacing against
    - period: 'M' (Month-to-Date), 'Q' (Quarter-to-Date), 'Y' (Year-to-Date)
    - as_of_date: Optional evaluation date (defaults to max date in df)
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    df = df.dropna(subset=[date_col, metric_col])
    if len(df) == 0:
        raise ValueError("DataFrame has no valid dates or metrics.")

    eval_date = pd.to_datetime(as_of_date) if as_of_date else df[date_col].max()

    period_clean = period.upper()
    if period_clean == "M":
        start_date = eval_date.replace(day=1)
        # End of month
        end_date = (start_date + pd.offsets.MonthEnd(1))
    elif period_clean == "Q":
        start_date = pd.Period(eval_date, freq="Q").start_time
        end_date = pd.Period(eval_date, freq="Q").end_time
    elif period_clean == "Y":
        start_date = eval_date.replace(month=1, day=1)
        end_date = eval_date.replace(month=12, day=31)
    else:
        raise ValueError("Period must be one of 'M', 'Q', or 'Y'.")

    # Filter to period
    period_df = df[(df[date_col] >= start_date) & (df[date_col] <= eval_date)]
    current_actual = float(period_df[metric_col].sum())

    days_elapsed = max(1, (eval_date.date() - start_date.date()).days + 1)
    total_days = max(1, (end_date.date() - start_date.date()).days + 1)
    days_remaining = max(0, total_days - days_elapsed)

    daily_velocity = current_actual / days_elapsed
    projected_run_rate = daily_velocity * total_days

    metrics = {
        "period": [f"{period_clean}TD ({start_date.strftime('%Y-%m-%d')} to {eval_date.strftime('%Y-%m-%d')})"],
        "actual_to_date": [round(current_actual, 2)],
        "days_elapsed": [days_elapsed],
        "total_days": [total_days],
        "days_remaining": [days_remaining],
        "daily_velocity": [round(daily_velocity, 2)],
        "projected_run_rate": [round(projected_run_rate, 2)],
    }

    if target is not None:
        pacing_pct = (projected_run_rate / target * 100.0) if target > 0 else 0.0
        remaining_gap = max(0.0, target - current_actual)
        needed_daily = (remaining_gap / days_remaining) if days_remaining > 0 else 0.0
        metrics["target"] = [target]
        metrics["pacing_pct"] = [round(pacing_pct, 1)]
        metrics["required_daily_run_rate"] = [round(needed_daily, 2)]

    return pd.DataFrame(metrics)
