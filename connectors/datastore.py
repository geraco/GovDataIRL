"""CKAN DataStore connector. Real datastore-backed resources aren't always
labelled format=API in the CKAN metadata (many are CSV/DB_TABLE with
datastore_active=true) — the discovery layer treats datastore_active as the
real signal, this connector just needs a resource id + host.

The CKAN datastore "dump" endpoint accepts format=json and works directly
against whichever CKAN instance hosts the resource (data.gov.ie,
opendata.agriculture.gov.ie, data.smartdublin.ie, ...) without needing to
know the action-API base URL for that host.
"""
import re

import httpx
import pandas as pd

from .base import Connector, NotNarrable, source_notes
from config import ROW_CAP


class DataStoreConnector(Connector):
    shape = "datastore"

    def fetch(self, resource: dict, package: dict, limit: int = ROW_CAP):
        dump_url = self._dump_url(resource)
        try:
            resp = httpx.get(dump_url, params={"limit": limit, "format": "json"}, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            raise NotNarrable(f"datastore dump fetch failed: {e}")

        fields = [f["id"] for f in payload.get("fields", []) if f["id"] != "_id"]
        records = payload.get("records", [])
        if not records or len(fields) < 2:
            raise NotNarrable("datastore dump has < 2 usable columns or no rows")

        col_index = {f["id"]: i for i, f in enumerate(payload["fields"])}
        rows = [[r[col_index[f]] for f in fields] for r in records]
        df = pd.DataFrame(rows, columns=fields)
        return df, source_notes(resource, package)

    @staticmethod
    def _dump_url(resource: dict) -> str:
        url = resource.get("url", "")
        m = re.search(r"(https?://[^/]+)", url)
        host = m.group(1) if m else ""
        return f"{host}/datastore/dump/{resource['id']}"
