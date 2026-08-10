"""Deterministic profiling engine — spec §5.3. No AI here: this is the
ground truth the analyst pipeline is required to cite and Pass C verifies
against. Returns a plain-JSON-serialisable dict.
"""
import numpy as np
import pandas as pd

SAMPLE_ROWS = 20
CORRELATION_THRESHOLD = 0.5


def _coerce_temporal(series: pd.Series) -> pd.Series | None:
    try:
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    except Exception:
        return None
    if parsed.notna().mean() < 0.7:
        return None
    return parsed


def profile_dataframe(df: pd.DataFrame) -> dict:
    df = df.copy()
    profile = {"row_count": len(df), "column_count": df.shape[1], "columns": {}}

    numeric_cols, temporal_col = [], None

    for col in df.columns:
        series = df[col]
        null_pct = round(series.isna().mean() * 100, 2)
        entry = {"dtype": str(series.dtype), "null_pct": null_pct, "cardinality": int(series.nunique())}

        if pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(col)
            desc = series.describe()
            entry.update(
                min=_num(desc.get("min")), max=_num(desc.get("max")),
                mean=_num(desc.get("mean")), median=_num(series.median()),
                stddev=_num(desc.get("std")),
            )
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
            entry["outlier_count"] = int(outliers.shape[0])
        else:
            temporal = _coerce_temporal(series) if temporal_col is None else None
            if temporal is not None:
                temporal_col = col
                entry["detected_type"] = "temporal"
                entry["date_range"] = [str(temporal.min().date()), str(temporal.max().date())]
            else:
                entry["detected_type"] = "categorical"
                top = series.value_counts().head(10)
                entry["top_values"] = {str(k): int(v) for k, v in top.items()}

        profile["columns"][col] = entry

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        pairs = []
        for i, a in enumerate(numeric_cols):
            for b in numeric_cols[i + 1:]:
                r = corr.loc[a, b]
                if pd.notna(r) and abs(r) >= CORRELATION_THRESHOLD:
                    pairs.append({"a": a, "b": b, "correlation": round(float(r), 3)})
        profile["correlations"] = sorted(pairs, key=lambda p: -abs(p["correlation"]))

    value_candidates = [c for c in numeric_cols if not any(
        k in c.lower() for k in ("year", "week", "date", "period", "month", "day")
    )] or numeric_cols
    if temporal_col and value_candidates:
        profile["time_series"] = _resample(df, temporal_col, value_candidates[0])

    profile["sample"] = _json_safe(df.sample(min(SAMPLE_ROWS, len(df)), random_state=1)).to_dict(orient="records")
    profile["sample_note"] = f"Illustrative sample of {min(SAMPLE_ROWS, len(df))} of {len(df)} total rows — not the full population."

    return profile


def _resample(df: pd.DataFrame, temporal_col: str, value_col: str) -> dict:
    ts = df[[temporal_col, value_col]].copy()
    ts[temporal_col] = pd.to_datetime(ts[temporal_col], errors="coerce", format="mixed")
    ts = ts.dropna().set_index(temporal_col).sort_index()
    if ts.empty:
        return {}
    span_days = (ts.index.max() - ts.index.min()).days
    freq = "YE" if span_days > 730 else ("ME" if span_days > 60 else "D")
    agg = ts[value_col].resample(freq).mean().dropna()
    pct_change = agg.pct_change().mul(100).round(2)
    return {
        "value_field": value_col,
        "granularity": freq,
        "periods": [str(i.date()) for i in agg.index],
        "values": [_num(v) for v in agg.values],
        "period_over_period_pct_change": [_num(v) for v in pct_change.values],
    }


def _num(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def _json_safe(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(df.notna(), None)
