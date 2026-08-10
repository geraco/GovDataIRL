"""Candidate pool builder + weighted-random pick. Entry points used by run.py."""
import random
from datetime import datetime, timedelta, timezone

from config import INTERESTINGNESS_THRESHOLD, RECENCY_EXCLUSION_DAYS
from db.store import connect, upsert
from discovery.probe import probe_all, pull_candidate_packages
from discovery.scoring import score


def refresh_candidate_pool():
    """Rebuild the full candidate pool. Cheap enough to run each time in v1
    (19-ish API-tagged packages on data.gov.ie) — spec's weekly/nightly split
    matters more at larger catalogue sizes than this one currently has."""
    packages = pull_candidate_packages()
    rows = probe_all(packages)
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        for row in rows:
            row["interestingness_score"] = score(row)
            row["last_probed_at"] = now
            upsert(conn, "candidates", row)
    return rows


def pick_dataset() -> dict | None:
    """Weighted-random pick from the scored pool, excluding recent picks."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RECENCY_EXCLUSION_DAYS)).isoformat()
    with connect() as conn:
        recent = {
            r["resource_id"]
            for r in conn.execute(
                "SELECT resource_id FROM runs WHERE status='success' AND started_at >= ?", (cutoff,)
            )
        }
        pool = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM candidates WHERE interestingness_score >= ? AND reachable = 1",
                (INTERESTINGNESS_THRESHOLD,),
            )
            if r["resource_id"] not in recent
        ]

    if not pool:
        return None

    weights = [max(row["interestingness_score"], 1) for row in pool]
    return random.choices(pool, weights=weights, k=1)[0]
