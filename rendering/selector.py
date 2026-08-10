"""visualisationSelector() — spec §7/§8 of the visualisation spec.

Deterministic: maps each ranked insight (profiling/insights.py) onto one of
a pragmatic subset of the catalogue (KPI/hero stat is handled separately in
the template; here: annotated trend line, lollipop ranking/concentration,
histogram distribution, quadrant-free scatter for relationships). Binding
chart data straight from the real dataframe means a hallucinated field name
is structurally impossible — the AI never chooses fields, only which
insights matter (see analyst/pipeline.py).
"""
import pandas as pd

from profiling.naming import humanize_label

MAX_CHARTS = 3


def select_charts(insights: list[dict], df: pd.DataFrame) -> list[dict]:
    charts = []
    seen_categories = set()
    for insight in insights:
        if len(charts) >= MAX_CHARTS:
            break
        if insight["category"] in seen_categories and insight["category"] != "concentration":
            continue  # diversity of chart types over repeating the same category
        spec = _build_spec(insight, df)
        if spec:
            charts.append(spec)
            seen_categories.add(insight["category"])
    return charts


def _title(insight: dict) -> str:
    d = insight["description"]
    return d[0].upper() + d[1:] if d else "Untitled finding"


def _build_spec(insight: dict, df: pd.DataFrame) -> dict | None:
    cat = insight["category"]
    if cat == "trend":
        cd = insight["chart_data"]
        return {
            "chart_type": "line_annotated", "title": _title(insight),
            "data": {"periods": cd["periods"], "values": cd["values"]},
            "annotation_index": insight.get("annotation_index", len(cd["values"]) - 1),
            "value_field": humanize_label(cd["value_field"]),
        }

    if cat in ("ranking", "concentration"):
        cd = insight["chart_data"]
        if "labels" in cd and "values" in cd:
            labels, values = cd["labels"], cd["values"]
        else:
            labels, values = list(cd["labels"]), list(cd["counts"])
        return {"chart_type": "lollipop", "title": _title(insight), "data": {"labels": labels, "values": values}}

    if cat == "correlation":
        a, b = insight["chart_data"]["x_field"], insight["chart_data"]["y_field"]
        if a not in df.columns or b not in df.columns:
            return None
        pair = df[[a, b]].dropna()
        if len(pair) < 3:
            return None
        return {
            "chart_type": "scatter", "title": _title(insight),
            "data": {"x": pair[a].tolist(), "y": pair[b].tolist()},
            "x_field": humanize_label(a), "y_field": humanize_label(b),
        }

    if cat == "outlier":
        field = insight["field"]
        if field not in df.columns:
            return None
        values = pd.to_numeric(df[field], errors="coerce").dropna().tolist()
        if len(values) < 5:
            return None
        return {"chart_type": "histogram", "title": _title(insight), "data": {"values": values}, "field": humanize_label(field)}

    return None
