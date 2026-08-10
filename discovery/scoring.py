"""Interestingness scoring — spec §5.1. Simple weighted heuristic, tunable."""

SWEET_SPOT_MIN, SWEET_SPOT_MAX = 50, 500_000


def score(row: dict) -> int:
    if not row.get("reachable"):
        return -40

    s = 0
    if row.get("has_temporal"):
        s += 30
    if row.get("has_numeric"):
        s += 20  # counted once here; spec's ">=2 numeric fields" needs col count, see below
    if row.get("has_categorical"):
        s += 15
    if SWEET_SPOT_MIN <= (row.get("row_estimate") or 0) <= SWEET_SPOT_MAX:
        s += 15
    if row.get("col_estimate", 0) <= 1:
        s -= 25  # effectively geometry-only / no usable attributes
    if (row.get("row_estimate") or 0) <= 1:
        s -= 20  # single-row / static lookup
    return s
