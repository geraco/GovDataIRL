"""Analytical insight engine — spec §17 of the visualisation spec.

Runs on the deterministic profile (never the AI), so every insight is a
real, computed fact: biggest change, concentration, correlation, outliers,
historical high/low. Each insight carries a `magnitude` for ranking and a
`category` used by rendering/selector.py to pick a chart type — this is
what lets the pipeline lead with "what's actually interesting" instead of
whatever the AI happens to describe first.
"""
from .profiler import non_date_like_columns


def detect_insights(df, profile: dict) -> list[dict]:
    insights = []

    ts = profile.get("time_series")
    if ts and ts.get("values"):
        insights.extend(_trend_insights(ts))

    for col, info in profile["columns"].items():
        if info.get("detected_type") == "categorical" and info.get("top_values"):
            insight = _concentration_insight(col, info, profile["row_count"])
            if insight:
                insights.append(insight)
        if info.get("outlier_count"):
            insight = _outlier_insight(col, info, profile["row_count"])
            if insight:
                insights.append(insight)

    real_measures = set(non_date_like_columns(list(profile["columns"].keys())))
    for pair in profile.get("correlations", []):
        if pair["a"] in real_measures and pair["b"] in real_measures:
            insights.append(_correlation_insight(pair))
            if len([i for i in insights if i["category"] == "correlation"]) >= 2:
                break

    insights.extend(_ranking_insights(df, profile))

    insights = [i for i in insights if i]
    insights.sort(key=lambda i: -i["magnitude"])
    return insights


def _trend_insights(ts: dict) -> list[dict]:
    out = []
    values = [v for v in ts["values"] if v is not None]
    periods = ts["periods"]
    if len(values) < 2:
        return out

    first, last = values[0], values[-1]
    if first:
        overall_pct = (last - first) / abs(first) * 100
        out.append({
            "category": "trend", "field": ts["value_field"],
            "magnitude": abs(overall_pct),
            "description": (
                f"{ts['value_field']} {'rose' if overall_pct >= 0 else 'fell'} "
                f"{abs(round(overall_pct))}% from {periods[0]} to {periods[-1]} "
                f"({round(first, 2)} → {round(last, 2)})."
            ),
            "chart_data": {"periods": periods, "values": ts["values"], "value_field": ts["value_field"]},
            "annotation_index": len(values) - 1,
        })

    changes = ts.get("period_over_period_pct_change") or []
    indexed = [(i, c) for i, c in enumerate(changes) if c is not None]
    if indexed:
        peak_i, peak_c = max(indexed, key=lambda x: abs(x[1]))
        out.append({
            "category": "trend", "field": ts["value_field"],
            "magnitude": abs(peak_c) * 1.1,  # single-period spikes usually more newsworthy than the overall trend
            "description": (
                f"The sharpest period-over-period move in {ts['value_field']} was "
                f"{'+' if peak_c >= 0 else ''}{round(peak_c)}% at {periods[peak_i]}."
            ),
            "chart_data": {"periods": periods, "values": ts["values"], "value_field": ts["value_field"]},
            "annotation_index": peak_i,
        })

    max_v, max_i = max((v, i) for i, v in enumerate(ts["values"]) if v is not None)
    out.append({
        "category": "trend", "field": ts["value_field"],
        "magnitude": 5,  # low-priority tiebreaker unless nothing else is going on
        "description": f"{ts['value_field']} peaked at {round(max_v, 2)} in {periods[max_i]}.",
        "chart_data": {"periods": periods, "values": ts["values"], "value_field": ts["value_field"]},
        "annotation_index": max_i,
    })
    return out


def _concentration_insight(col: str, info: dict, row_count: int) -> dict | None:
    top = info["top_values"]
    if not top or row_count == 0:
        return None
    if info.get("cardinality", 0) < 3:
        return None  # a lopsided yes/no split is structural noise, not a "one category dominates" story
    leader, leader_n = next(iter(top.items()))
    share = leader_n / row_count * 100
    if share < 20:  # not concentrated enough to be a "one thing dominates" story
        return None
    return {
        "category": "concentration", "field": col,
        "magnitude": share,
        "description": f"'{leader}' accounts for {round(share)}% of all {col} values ({leader_n} of {row_count}).",
        "chart_data": {"labels": list(top.keys()), "counts": list(top.values()), "field": col},
    }


def _outlier_insight(col: str, info: dict, row_count: int) -> dict | None:
    n = info["outlier_count"]
    if not n or row_count == 0:
        return None
    ratio = n / row_count * 100
    if ratio < 2:
        return None
    return {
        "category": "outlier", "field": col,
        "magnitude": ratio + 10,  # data-quality findings are usually genuinely noteworthy
        "description": f"{n} of {row_count} {col} values ({round(ratio, 1)}%) are statistical outliers (outside 1.5× IQR).",
        "chart_data": {"field": col},
    }


def _correlation_insight(pair: dict) -> dict:
    strength = "strong" if abs(pair["correlation"]) >= 0.8 else "moderate"
    direction = "positive" if pair["correlation"] > 0 else "negative"
    return {
        "category": "correlation", "field": f"{pair['a']}__{pair['b']}",
        "magnitude": abs(pair["correlation"]) * 60,
        "description": f"{pair['a']} and {pair['b']} show a {strength} {direction} correlation (r={pair['correlation']}).",
        "chart_data": {"x_field": pair["a"], "y_field": pair["b"]},
    }


def _ranking_insights(df, profile: dict) -> list[dict]:
    """Aggregate the primary numeric measure by each low-cardinality
    categorical column, and flag the leader-vs-runner-up gap when it's
    large enough to be a real finding."""
    out = []
    all_numeric = [c for c, i in profile["columns"].items() if "mean" in i]
    numeric_cols = non_date_like_columns(all_numeric)
    cat_cols = [c for c, i in profile["columns"].items()
                if i.get("detected_type") == "categorical" and 1 < i["cardinality"] <= 15]
    if not numeric_cols or not cat_cols:
        return out

    value_col = numeric_cols[0]
    for cat_col in cat_cols[:2]:
        try:
            agg = df.groupby(cat_col)[value_col].sum().sort_values(ascending=False)
        except Exception:
            continue
        if len(agg) < 2 or agg.iloc[0] <= 0:
            continue
        gap_pct = (agg.iloc[0] - agg.iloc[1]) / agg.iloc[0] * 100
        out.append({
            "category": "ranking", "field": f"{cat_col}__{value_col}",
            "magnitude": gap_pct * 0.8,
            "description": (
                f"By total {value_col}, '{agg.index[0]}' leads all {cat_col} categories "
                f"with {round(agg.iloc[0], 1)}, {round(gap_pct)}% ahead of runner-up '{agg.index[1]}' "
                f"({round(agg.iloc[1], 1)})."
            ),
            "chart_data": {
                "labels": [str(k) for k in agg.head(8).index], "values": [round(float(v), 3) for v in agg.head(8).values],
                "cat_field": cat_col, "value_field": value_col,
            },
        })
    return out
