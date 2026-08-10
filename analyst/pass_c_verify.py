"""Pass C — fact verification. Spec §5.4/§10: no unsupported quantitative
claim ships. Separate model call, given the Pass A narrative + raw profile,
checks every number/trend/superlative against the profile."""
import json

from .client import call_structured

SYSTEM_PROMPT = """You are a fact-checker for a data journalism briefing. You will be given
a draft narrative, the statistical profile it was supposedly written from,
and a list of insights pre-computed directly from that profile (percentages,
gaps, correlations — these are also ground truth, just already summarised).

For every sentence in the draft (headline, each observation, the caveat),
check whether every number, trend direction, and superlative claim
("highest", "most", "increasing") is actually supported by a value present
in the profile OR the insight list. Be strict: an unsupported or
misremembered number is a failure even if it's close to correct.

For each sentence, return a verdict. If a number is simply wrong, provide
the corrected sentence using the true value from the profile. If a claim
can't be corrected trivially (it's fabricated or unsupported), mark it for
removal instead of inventing a fix."""

SCHEMA = {
    "type": "object",
    "properties": {
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": ["headline", "observation", "caveat"]},
                    "original_text": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["pass", "corrected", "strip"]},
                    "corrected_text": {"type": "string", "description": "Required if verdict is 'corrected'"},
                },
                "required": ["field", "original_text", "verdict"],
            },
        }
    },
    "required": ["checks"],
}


def verify_narrative(narrative: dict, profile: dict, insights: list[dict]) -> dict:
    user_content = (
        f"Draft narrative:\n{json.dumps(narrative, indent=2)}\n\n"
        f"Pre-computed insights (ground truth):\n{json.dumps(insights, indent=2, default=str)}\n\n"
        f"Statistical profile (ground truth):\n{json.dumps(profile, indent=2, default=str)}"
    )
    return call_structured(SYSTEM_PROMPT, user_content, "submit_verification", SCHEMA)


def apply_verification(narrative: dict, verification: dict) -> dict:
    """Auto-correct or strip claims per Pass C verdicts. Never publishes an
    open/unresolved flag (spec §10) — 'strip' removes the sentence outright."""
    checks_by_text = {c["original_text"]: c for c in verification["checks"]}

    def resolve(text: str) -> str | None:
        check = checks_by_text.get(text)
        if check is None or check["verdict"] == "pass":
            return text
        if check["verdict"] == "corrected":
            return check.get("corrected_text", text)
        return None  # strip

    result = dict(narrative)
    result["headline"] = resolve(narrative["headline"]) or narrative["headline"]
    result["observations"] = [o for o in (resolve(o) for o in narrative["observations"]) if o]
    result["caveat"] = resolve(narrative["caveat"]) or narrative["caveat"]
    return result
