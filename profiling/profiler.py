"""Deterministic profiling engine — spec §5.3. No AI here: this is the
ground truth the analyst pipeline is required to cite and Pass C verifies
against. Returns a plain-JSON-serialisable dict.
"""
import re

import numpy as np
import pandas as pd

SAMPLE_ROWS = 20
CORRELATION_THRESHOLD = 0.5

NON_MEASURE_NAME_MARKERS = (
    "year", "week", "date", "period", "month", "day",
    "easting", "northing", "lat", "lon", "latitude", "longitude", "geo",
)
# Three separate id-shapes seen in real data.gov.ie resources: underscore/space
# separated ("STATION ID", "object_id"), camelCase suffix ("BikeID", "StationId"),
# and spelled out ("BikeIdentifier"). All three have hit real bugs — a column
# named this way is a row identifier, never a measure to aggregate/trend/correlate.
ID_LIKE_WORD_PATTERN = re.compile(r"(^|[_\s])id(s)?($|[_\s])", re.IGNORECASE)
ID_LIKE_CAMEL_PATTERN = re.compile(r"[a-z](id)$")
ADMIN_TIMESTAMP_MARKERS = ("last_updated", "modified", "created", "timestamp", "updated_at", "edited")


def _is_id_like(col: str) -> bool:
    return bool(ID_LIKE_WORD_PATTERN.search(col)) or bool(ID_LIKE_CAMEL_PATTERN.search(col.lower())) \
        or "identifier" in col.lower()


def non_date_like_columns(columns: list[str]) -> list[str]:
    """Filters out numeric columns whose *name* looks like a calendar field,
    an identifier, or a geographic coordinate — these aren't measures, and
    picking one as a chart's value axis produces a nonsense chart (real bug
    hit repeatedly: YEAR resampled as a value, easting plotted as a trend,
    "STATION ID"/"BikeID"/"BikeIdentifier" aggregated and reported as if they
    measured something). No fallback to the unfiltered list on purpose — a
    dataset with no real measure column should get no trend/ranking insight
    rather than a fabricated one built from an ID or coordinate."""
    return [c for c in columns
            if not any(k in c.lower() for k in NON_MEASURE_NAME_MARKERS)
            and not _is_id_like(c)]


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

    numeric_cols, temporal_candidates = [], []

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
            temporal = _coerce_temporal(series)
            if temporal is not None:
                temporal_candidates.append((col, temporal))
                entry["detected_type"] = "temporal"
                entry["date_range"] = [str(temporal.min().date()), str(temporal.max().date())]
            else:
                entry["detected_type"] = "categorical"
                top = series.value_counts().head(10)
                entry["top_values"] = {str(k): int(v) for k, v in top.items()}

        profile["columns"][col] = entry

    # Prefer a genuine observation date over an admin edit/metadata timestamp
    # (e.g. "last_updated" on a location registry isn't a real time axis).
    temporal_col = None
    if temporal_candidates:
        domain_dates = [c for c, _ in temporal_candidates
                         if not any(m in c.lower() for m in ADMIN_TIMESTAMP_MARKERS)]
        temporal_col = domain_dates[0] if domain_dates else temporal_candidates[0][0]

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        pairs = []
        for i, a in enumerate(numeric_cols):
            for b in numeric_cols[i + 1:]:
                r = corr.loc[a, b]
                if pd.notna(r) and abs(r) >= CORRELATION_THRESHOLD:
                    pairs.append({"a": a, "b": b, "correlation": round(float(r), 3)})
        profile["correlations"] = sorted(pairs, key=lambda p: -abs(p["correlation"]))

    value_candidates = non_date_like_columns(numeric_cols)
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


def data_period_label(profile: dict) -> str | None:
    """The date range the *data itself* covers (from a detected temporal
    column), not when the dataset listing was last edited — those are often
    very different (e.g. a 2014 water-quality snapshot re-published in 2025)."""
    for info in profile["columns"].values():
        date_range = info.get("date_range")
        if date_range:
            start, end = date_range
            if start[:4] == end[:4]:
                return start[:4]
            return f"{start[:4]}–{end[:4]}"
    return None


def _num(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def _json_safe(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(df.notna(), None)
