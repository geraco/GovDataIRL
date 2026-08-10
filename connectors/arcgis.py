"""ArcGIS FeatureServer/MapServer connector.

Query shape: GET {layer_url}/query?where=1=1&outFields=*&f=json
Response: {"features": [{"attributes": {...}, "geometry": {...}}, ...]}
The analytical dataframe keeps `attributes` only — geometry isn't
narratable for this tool's purposes (per spec §5.2).
"""
import httpx
import pandas as pd

from .base import Connector, NotNarrable, source_notes


class ArcGISConnector(Connector):
    shape = "arcgis"

    def fetch(self, resource: dict, package: dict, **_):
        base_url = resource.get("url", "").rstrip("/")
        query_url = base_url if base_url.endswith("query") else f"{base_url}/query"
        params = {"where": "1=1", "outFields": "*", "f": "json", "resultRecordCount": 20000}
        try:
            resp = httpx.get(query_url, params=params, timeout=30)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            raise NotNarrable(f"arcgis query failed: {e}")

        if "error" in payload:
            raise NotNarrable(f"arcgis returned error: {payload['error']}")

        features = payload.get("features", [])
        attrs = [f.get("attributes", {}) for f in features]
        if not attrs:
            raise NotNarrable("no features returned")

        df = pd.DataFrame(attrs)
        non_id_cols = [c for c in df.columns if not c.lower().endswith("objectid")]
        if len(non_id_cols) < 2:
            raise NotNarrable("fewer than 2 non-geometry attribute columns")

        return df[non_id_cols], source_notes(resource, package)
