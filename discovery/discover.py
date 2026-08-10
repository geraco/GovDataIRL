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
    """Weighted-random pick from the scored pool, excluding recently-published
    *datasets* (package_id) — not just resource_id. A single CKAN package
    routinely has several resource_ids (e.g. "Bathing Water API" has separate
    locations/measurements/alerts endpoints); excluding only by resource_id
    let the same named dataset get re-published repeatedly via a different
    underlying resource, which reads as a duplicate story to a reader even
    though no individual resource_id was technically repeated."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RECENCY_EXCLUSION_DAYS)).isoformat()
    with connect() as conn:
        recent_packages = {
            r["package_id"]
            for r in conn.execute(
                """SELECT DISTINCT c.package_id FROM runs r
                   JOIN candidates c ON c.resource_id = r.resource_id
                   WHERE r.status = 'success' AND r.started_at >= ?""",
                (cutoff,),
            )
        }
        pool = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM candidates WHERE interestingness_score >= ? AND reachable = 1",
                (INTERESTINGNESS_THRESHOLD,),
            )
            if r["package_id"] not in recent_packages
        ]

    if not pool:
        return None

    weights = [max(row["interestingness_score"], 1) for row in pool]
    return random.choices(pool, weights=weights, k=1)[0]
