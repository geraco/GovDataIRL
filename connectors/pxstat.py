"""CSO PxStat / PX-Web connector — JSON-stat 2.0 format.

PxStat payloads look like:
{"dataset": {"dimension": {"STATISTIC": {...}, "TLIST(A1)": {...}, ...},
             "id": ["STATISTIC", "TLIST(A1)", ...],
             "size": [2, 10, ...],
             "value": [123, 456, null, ...]}}

Dimensions are unpivoted into a tidy long-format dataframe: one row per
value, one column per dimension label + a "value" column. This is the
standard JSON-stat -> tidy-dataframe transform.
"""
import itertools

import httpx
import pandas as pd

from .base import Connector, NotNarrable, source_notes


class PxStatConnector(Connector):
    shape = "pxstat"

    def fetch(self, resource: dict, package: dict, **_):
        url = resource.get("url", "")
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            raise NotNarrable(f"pxstat fetch failed: {e}")

        dataset = payload.get("dataset", payload)
        dim_ids = dataset.get("id") or dataset.get("dimension", {}).get("id")
        sizes = dataset.get("size")
        dimension = dataset.get("dimension")
        values = dataset.get("value")
        if not (dim_ids and sizes and dimension and values is not None):
            raise NotNarrable("payload is not a recognisable JSON-stat dataset")

        labels_per_dim = []
        for dim_id in dim_ids:
            cat = dimension[dim_id]["category"]
            index = cat.get("index")
            label_map = cat.get("label", {})
            if isinstance(index, dict):
                ordered_keys = sorted(index, key=lambda k: index[k])
            elif isinstance(index, list):
                ordered_keys = index
            else:
                ordered_keys = list(label_map.keys())
            labels_per_dim.append([label_map.get(k, k) for k in ordered_keys])

        combos = itertools.product(*labels_per_dim)
        rows = []
        for combo, value in zip(combos, values):
            if value is None:
                continue
            rows.append(dict(zip(dim_ids, combo)) | {"value": value})

        if len(rows) < 5:
            raise NotNarrable("too few non-null JSON-stat values to be narratable")

        df = pd.DataFrame(rows)
        return df, source_notes(resource, package)
