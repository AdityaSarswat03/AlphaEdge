"""
Visualization helpers for charts and reports.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional


class Visualizer:
    """Generate interactive Plotly charts."""

    # ── Candlestick chart ────────────────────────────────────────
    @staticmethod
    def candlestick(
        df: pd.DataFrame,
        title: str = "Price Chart",
        show_volume: bool = True,
    ) -> go.Figure:
        rows = 2 if show_volume else 1
        heights = [0.7, 0.3] if show_volume else [1.0]
        fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            row_heights=heights,
            vertical_spacing=0.03,
        )
        fig.add_trace(
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
            ),
            row=1,
            col=1,
        )
        if show_volume and "Volume" in df.columns:
            colours = ["red" if c < o else "green" for c, o in zip(df["Close"], df["Open"])]
            fig.add_trace(
                go.Bar(x=df["Date"], y=df["Volume"], marker_color=colours, name="Volume"),
                row=2,
                col=1,
            )
        fig.update_layout(title=title, xaxis_rangeslider_visible=False, height=600)
        return fig

    # ── Equity curve ─────────────────────────────────────────────
    @staticmethod
    def equity_curve(
        equity: List[float],
        dates: Optional[pd.Series] = None,
        title: str = "Portfolio Equity Curve",
    ) -> go.Figure:
        x = dates if dates is not None else list(range(len(equity)))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=equity, mode="lines", name="Equity"))
        fig.update_layout(title=title, yaxis_title="Portfolio Value (₹)", height=400)
        return fig

    # ── Prediction chart ─────────────────────────────────────────
    @staticmethod
    def prediction_chart(
        historical: pd.Series,
        predicted: float,
        lower: float,
        upper: float,
        ticker: str = "",
    ) -> go.Figure:
        n = len(historical)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=historical.values, mode="lines", name="Historical"))
        fig.add_trace(
            go.Scatter(
                x=[n - 1, n],
                y=[historical.iloc[-1], predicted],
                mode="lines+markers",
                name="Predicted",
                line=dict(dash="dash", color="orange"),
            )
        )
        # Confidence band
        fig.add_trace(
            go.Scatter(
                x=[n, n],
                y=[lower, upper],
                mode="markers",
                name="Confidence Interval",
                marker=dict(size=10, symbol="line-ns-open", color="orange"),
            )
        )
        fig.update_layout(title=f"{ticker} Prediction", height=400)
        return fig

    # ── Feature importance bar chart ─────────────────────────────
    @staticmethod
    def feature_importance(
        features: List[Dict[str, Any]], title: str = "Feature Importance"
    ) -> go.Figure:
        names = [f["feature"] for f in features]
        vals = [f["importance"] for f in features]
        fig = go.Figure(go.Bar(x=vals, y=names, orientation="h"))
        fig.update_layout(title=title, height=400, yaxis=dict(autorange="reversed"))
        return fig
