"""Executes Pass B's chart specs against the real dataframe — spec §5.5.
Static SVG output (kaleido), fixed accent-derived palette, no client-side
charting dependency (spec §9)."""
import base64
import io

import pandas as pd
import plotly.graph_objects as go

from config import ACCENT_COLOUR

PALETTE = [ACCENT_COLOUR, "#C97C2A", "#3B6EA5", "#8A6BA8", "#5A5A55"]


def _aggregate(df: pd.DataFrame, spec: dict) -> pd.DataFrame:
    x, y, agg = spec["x_field"], spec.get("y_field"), spec["aggregation"]
    if x not in df.columns:
        raise ValueError(f"chart spec x_field '{x}' not in dataframe columns")
    if agg == "none":
        return df[[x] + ([y] if y and y in df.columns else [])].dropna()
    if agg == "count":
        count_col = "count" if not y or y == x else y
        return df.groupby(x).size().reset_index(name=count_col)
    if not y or y not in df.columns:
        raise ValueError(f"chart spec y_field '{y}' required for aggregation '{agg}' but missing/invalid")
    grouped = df.groupby(x)[y]
    series = {"sum": grouped.sum, "mean": grouped.mean}[agg]()
    return series.reset_index()


def render_chart(df: pd.DataFrame, spec: dict, index: int) -> str:
    """Returns an <img> tag with an inline base64 SVG — self-contained,
    archivable, no runtime chart library dependency."""
    data = _aggregate(df, spec)
    x_col = spec["x_field"]
    y_col = spec.get("y_field")
    if not y_col or y_col not in data.columns:
        y_col = data.columns[-1]
    colour = PALETTE[index % len(PALETTE)]

    kind = spec["chart_type"]
    if kind == "histogram":
        fig = go.Figure(go.Histogram(x=data[x_col], marker_color=colour))
    elif kind == "bar":
        fig = go.Figure(go.Bar(x=data[x_col], y=data[y_col], marker_color=colour))
    elif kind == "scatter":
        fig = go.Figure(go.Scatter(x=data[x_col], y=data[y_col], mode="markers", marker_color=colour))
    else:  # line
        fig = go.Figure(go.Scatter(x=data[x_col], y=data[y_col], mode="lines+markers", line_color=colour))

    fig.update_layout(
        title=spec["title"],
        font=dict(family="Inter, IBM Plex Sans, sans-serif", size=14, color="#1A1A18"),
        plot_bgcolor="#FAFAF7", paper_bgcolor="#FAFAF7",
        margin=dict(l=50, r=30, t=50, b=50),
        width=820, height=440,
    )

    svg_bytes = fig.to_image(format="svg")
    b64 = base64.b64encode(svg_bytes).decode("ascii")
    return f'<img class="report-chart" alt="{spec["title"]}" src="data:image/svg+xml;base64,{b64}">'


def render_all(df: pd.DataFrame, chart_specs: list[dict]) -> list[str]:
    tags = []
    for i, spec in enumerate(chart_specs):
        try:
            tags.append(render_chart(df, spec, i))
        except Exception:
            continue  # a bad chart spec is not worth failing the whole run over
    return tags
