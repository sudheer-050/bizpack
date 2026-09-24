"""
Pandas DataFrame accessor for BizKit.
Enables df.biz.clean(), df.biz.format(), df.biz.pareto(), etc.
"""

import pandas as pd
from typing import Optional, Union, List, Dict
from bizpack import cleaner, formulas, formatters


@pd.api.extensions.register_dataframe_accessor("biz")
class BizAccessor:
    """
    Custom pandas accessor exposing BizKit utilities directly on DataFrames.
    """

    def __init__(self, pandas_obj: pd.DataFrame):
        self._obj = pandas_obj

    def clean(
        self,
        headers: bool = True,
        strings: bool = True,
        totals: bool = True,
        empty: bool = True,
        types: bool = True,
        percent_as_ratio: bool = True,
    ) -> pd.DataFrame:
        """One-line data cleaning."""
        return cleaner.clean(
            self._obj,
            headers=headers,
            strings=strings,
            totals=totals,
            empty=empty,
            types=types,
            percent_as_ratio=percent_as_ratio,
        )

    def clean_headers(self) -> pd.DataFrame:
        return cleaner.clean_headers(self._obj)

    def clean_strings(self) -> pd.DataFrame:
        return cleaner.clean_strings(self._obj)

    def strip_totals(self) -> pd.DataFrame:
        return cleaner.strip_totals(self._obj)

    def drop_empty(self) -> pd.DataFrame:
        return cleaner.drop_empty(self._obj)

    def format(
        self,
        formats: Optional[Dict[str, str]] = None,
        currency_symbol: str = "$",
    ) -> pd.DataFrame:
        """Format numbers back to $, %, or accounting strings for presentation."""
        return formatters.format_for_display(
            self._obj,
            formats=formats,
            currency_symbol=currency_symbol,
        )

    def pareto(
        self,
        dim_col: str,
        metric_col: str,
        top_pct: float = 0.80,
    ) -> pd.DataFrame:
        """Run 80/20 Pareto analysis."""
        return formulas.pareto(self._obj, dim_col=dim_col, metric_col=metric_col, top_pct=top_pct)

    def growth(
        self,
        date_col: str,
        metric_col: str,
        freq: str = "M",
        group_by: Optional[Union[str, List[str]]] = None,
    ) -> pd.DataFrame:
        """Run MoM/YoY growth analysis."""
        return formulas.growth(
            self._obj,
            date_col=date_col,
            metric_col=metric_col,
            freq=freq,
            group_by=group_by,
        )

    def run_rate(
        self,
        date_col: str,
        metric_col: str,
        target: Optional[float] = None,
        period: str = "M",
    ) -> pd.DataFrame:
        """Calculate pacing and projected run-rate."""
        return formulas.run_rate(
            self._obj,
            date_col=date_col,
            metric_col=metric_col,
            target=target,
            period=period,
        )
