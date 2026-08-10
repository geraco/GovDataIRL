"""Three-pass pipeline orchestration — spec §5.4."""
from .pass_a_draft import draft_narrative
from .pass_b_charts import propose_charts
from .pass_c_verify import apply_verification, verify_narrative


def run_pipeline(metadata: dict, profile: dict) -> dict:
    draft = draft_narrative(metadata, profile)
    chart_specs = propose_charts(profile)["charts"]
    verification = verify_narrative(draft, profile)
    verified_narrative = apply_verification(draft, verification)

    if not verified_narrative["observations"]:
        raise RuntimeError("all observations stripped by fact-verification — nothing left to publish")

    return {
        "narrative": verified_narrative,
        "chart_specs": chart_specs,
        "raw_draft": draft,
        "verification": verification,
    }
