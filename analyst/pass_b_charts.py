"""Pass B — chart specification. Spec §5.4. The model proposes specs only;
the renderer executes them against the real dataframe (§5.5), so charts
can never show a hallucinated shape."""
import json

from .client import call_structured

SYSTEM_PROMPT = """You are choosing charts to accompany a data journalism briefing.
Given a dataset's statistical profile, propose 2-3 charts that best support
the narrative. You are NOT drawing the chart — only specifying it. The
renderer will execute your spec against the real data, so field names must
exactly match column names in the profile."""

SCHEMA = {
    "type": "object",
    "properties": {
        "charts": {
            "type": "array",
            "minItems": 1, "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "histogram"]},
                    "title": {"type": "string"},
                    "x_field": {"type": "string"},
                    "y_field": {"type": "string"},
                    "aggregation": {"type": "string", "enum": ["none", "sum", "mean", "count"]},
                },
                "required": ["chart_type", "title", "x_field", "aggregation"],
            },
        }
    },
    "required": ["charts"],
}


def propose_charts(profile: dict) -> dict:
    user_content = f"Statistical profile:\n{json.dumps(profile, indent=2, default=str)}"
    return call_structured(SYSTEM_PROMPT, user_content, "submit_chart_specs", SCHEMA)
