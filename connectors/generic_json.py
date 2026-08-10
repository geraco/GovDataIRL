"""Fallback for bespoke REST APIs (Valuation Office, EPA, local authorities...).
Fetches JSON, finds the most plausible top-level list of records, flattens it.
Raises NotNarrable if no rectangular shape with >=2 usable columns emerges —
the discovery engine re-rolls rather than publishing garbage.
"""
import httpx
import pandas as pd

from .base import Connector, NotNarrable, source_notes


def _find_record_list(payload):
    """Return the largest top-level list of dict records, or None."""
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload
    if not isinstance(payload, dict):
        return None
    candidates = [v for v in payload.values() if isinstance(v, list) and v and isinstance(v[0], dict)]
    if not candidates:
        return None
    return max(candidates, key=len)


class GenericJSONConnector(Connector):
    shape = "generic_json"

    def fetch(self, resource: dict, package: dict, **_):
        url = resource.get("url", "")
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            raise NotNarrable(f"generic json fetch failed: {e}")

        records = _find_record_list(payload)
        if not records:
            raise NotNarrable("no top-level list of record objects found")

        df = pd.json_normalize(records)
        usable_cols = [c for c in df.columns if df[c].notna().any()]
        df = df[usable_cols]
        if df.shape[1] < 2 or df.shape[0] < 5:
            raise NotNarrable(f"not rectangular enough: {df.shape}")

        return df, source_notes(resource, package)
