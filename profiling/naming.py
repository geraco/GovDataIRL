"""Turns raw column names (county_name, STATION ID, incident_expected_duration)
into readable labels for chart axes/titles and deterministic insight text.
Pure formatting — no semantic renaming — so it can't misrepresent a field.
The AI layer (Pass A) is separately instructed to go further and use natural
phrasing in prose (e.g. "county" instead of "County Name")."""
import re

_STRIP_SUFFIXES = ("_name", " name")


def humanize_label(raw: str) -> str:
    s = re.sub(r"[_\-]+", " ", raw).strip()
    s = re.sub(r"\s+", " ", s)
    # ALLCAPS or all-lower source -> title case; mixedCase left alone (already a real label)
    if s == s.upper() or s == s.lower():
        s = s.title()
    for suffix in _STRIP_SUFFIXES:
        if s.lower().endswith(suffix) and len(s) > len(suffix) + 2:
            s = s[: -len(suffix)]
            break
    return s
