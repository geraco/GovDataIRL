"""Pass A — analyst draft narrative. Spec §5.4 / §12."""
import json

from .client import call_structured

SYSTEM_PROMPT = """You are a senior public-sector data analyst writing a short public-facing
briefing about an Irish government open dataset. Your reader is intelligent
and curious but not a statistician.

You will be given:
- Dataset metadata (title, publisher, licence, last updated)
- A deterministic statistical profile of the dataset (computed in code —
  treat every number in this profile as ground truth)
- A capped sample of rows (illustrative only — NOT the full dataset;
  never treat the sample as complete)

Rules:
- Every number you state must come from the profile, not be estimated
  or invented
- Do not extrapolate beyond what the data supports
- Plain language over statistical jargon
- If the data is genuinely uninteresting, say so plainly rather than
  manufacturing a finding"""

SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "One-sentence headline finding"},
        "observations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3, "maxItems": 5,
            "description": "3-5 supporting observations, each grounded in a specific number from the profile",
        },
        "caveat": {"type": "string", "description": "One explicit caveat or limitation of this data"},
    },
    "required": ["headline", "observations", "caveat"],
}


def draft_narrative(metadata: dict, profile: dict) -> dict:
    user_content = (
        f"Dataset metadata:\n{json.dumps(metadata, indent=2)}\n\n"
        f"Statistical profile (ground truth):\n{json.dumps(profile, indent=2, default=str)}"
    )
    return call_structured(SYSTEM_PROMPT, user_content, "submit_narrative", SCHEMA)
