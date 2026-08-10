"""Universal connector layer — detects resource shape, dispatches to the
matching strategy. See §3.2 / §5.2 of the spec."""
from .arcgis import ArcGISConnector
from .base import NotNarrable
from .datastore import DataStoreConnector
from .generic_json import GenericJSONConnector
from .pxstat import PxStatConnector

_WFS_MARKERS = ("service=wfs", "/wfs", "wms?service=wms", "/wms")


def detect_shape(resource: dict) -> str:
    url = (resource.get("url") or "").lower()
    fmt = (resource.get("format") or "").lower()

    if resource.get("datastore_active"):
        return "datastore"
    if "jsonstat" in url or "pxstat" in url or "px-api" in url or "statbank" in url:
        return "pxstat"
    if "featureserver" in url or "mapserver" in url or "arcgis" in url:
        return "arcgis"
    if any(marker in url for marker in _WFS_MARKERS) or fmt in ("wfs", "wms"):
        return "wfs"
    if fmt in ("json", "api") or url.endswith(".json") or "api" in url:
        return "generic_json"
    return "unknown"


CONNECTORS = {
    "datastore": DataStoreConnector(),
    "pxstat": PxStatConnector(),
    "arcgis": ArcGISConnector(),
    "generic_json": GenericJSONConnector(),
}


def fetch(resource: dict, package: dict, **kwargs):
    """Detect shape and fetch. Raises NotNarrable for wfs/unknown/failed shapes."""
    shape = detect_shape(resource)
    connector = CONNECTORS.get(shape)
    if connector is None:
        raise NotNarrable(f"shape '{shape}' has no connector (v1 skips WFS/unknown)")
    return connector.fetch(resource, package, **kwargs)
