"""Connector strategy interface. Every connector turns CKAN resource metadata
into (dataframe, source_notes) or raises NotNarrable."""
import pandas as pd


class NotNarrable(Exception):
    """Raised when a resource can't be turned into a usable dataframe."""


class SourceNotes(dict):
    """source_notes = {url, licence, last_updated, publisher}"""


def source_notes(resource: dict, package: dict) -> dict:
    return {
        "url": resource.get("url", ""),
        "licence": package.get("license_title") or package.get("license_id") or "Unknown",
        "last_updated": package.get("metadata_modified", ""),
        "publisher": (package.get("organization") or {}).get("title", "Unknown"),
    }


class Connector:
    shape = "base"

    def fetch(self, resource: dict, package: dict) -> tuple[pd.DataFrame, dict]:
        raise NotImplementedError
