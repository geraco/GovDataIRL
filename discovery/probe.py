"""Pull the candidate pool from CKAN, probe each resource for viability.

Pool = res_format:API search (the documented surface) plus a
resource_search for datastore_active:true (many real DataStore resources
aren't labelled format=API — confirmed against live data.gov.ie, e.g. CSV
resources with datastore_active=true). Both are CKAN Action API endpoints
listed in spec §3.1.
"""
import time

import httpx
import pandas as pd

from config import CKAN_BASE, CKAN_REQUEST_DELAY_SECONDS
from connectors import NotNarrable, detect_shape, fetch as connector_fetch


PROBE_ROW_LIMIT = 200      # viability probe only needs enough rows to detect shape/dtypes
MAX_RESOURCES_PER_PACKAGE = 6  # packages like dublinbikes ship 100+ monthly CSV dumps; probe a sample


def _ckan_get(action: str, **params) -> dict:
    resp = httpx.get(f"{CKAN_BASE}/{action}", params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN {action} failed: {payload}")
    return payload["result"]


def pull_candidate_packages() -> list[dict]:
    """Returns full CKAN package dicts (with nested resources) for every
    package that has at least one API-shaped or datastore-active resource."""
    seen = {}

    result = _ckan_get("package_search", fq="res_format:API", rows=200)
    for pkg in result["results"]:
        seen[pkg["id"]] = pkg

    try:
        result = _ckan_get("resource_search", query="datastore_active:true")
    except Exception:
        result = {"results": []}  # this endpoint 409s on some CKAN versions — pool still works without it
    for res in result.get("results", []):
        pkg_id = res.get("package_id")
        if pkg_id and pkg_id not in seen:
            try:
                seen[pkg_id] = _ckan_get("package_show", id=pkg_id)
            except Exception:
                continue

    return list(seen.values())


def probe_resource(resource: dict, package: dict) -> dict:
    """Lightweight viability probe: attempt a real fetch (small/cheap by
    connector design) and record the profile-relevant flags."""
    shape = detect_shape(resource)
    row = {
        "resource_id": resource["id"],
        "package_id": package["id"],
        "package_name": package.get("name", ""),
        "title": package.get("title", resource.get("name", "")),
        "publisher": (package.get("organization") or {}).get("title", "Unknown"),
        "licence": package.get("license_title") or package.get("license_id") or "Unknown",
        "resource_url": resource.get("url", ""),
        "resource_format": resource.get("format", ""),
        "shape": shape,
        "package_notes": (package.get("notes") or "")[:2000],
        "package_last_modified": package.get("metadata_modified", ""),
    }

    try:
        df, _ = connector_fetch(resource, package, limit=PROBE_ROW_LIMIT)
        row["reachable"] = True
        row["row_estimate"] = len(df)
        row["col_estimate"] = df.shape[1]
        row["has_numeric"] = df.select_dtypes(include="number").shape[1] >= 2
        row["has_temporal"] = _has_temporal(df)
        row["has_categorical"] = _has_categorical(df)
    except (NotNarrable, Exception) as e:
        row.update(reachable=False, row_estimate=0, col_estimate=0,
                    has_numeric=False, has_temporal=False, has_categorical=False)
        row["shape"] = "unreachable" if shape == "unknown" else shape

    return row


def _has_temporal(df: pd.DataFrame) -> bool:
    name_hits = any(k in c.lower() for c in df.columns for k in ("date", "year", "time", "period"))
    return name_hits


def _has_categorical(df: pd.DataFrame) -> bool:
    for c in df.columns:
        if df[c].dtype == object and 1 < df[c].nunique() <= max(50, len(df) * 0.5):
            return True
    return False


def probe_all(packages: list[dict]) -> list[dict]:
    rows = []
    for pkg in packages:
        narratable_resources = [r for r in pkg.get("resources", []) if detect_shape(r) != "wfs"]
        for resource in narratable_resources[:MAX_RESOURCES_PER_PACKAGE]:
            rows.append(probe_resource(resource, pkg))
            time.sleep(CKAN_REQUEST_DELAY_SECONDS)
    return rows
