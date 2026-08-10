"""Two-pass AI pipeline (draft + verify) plus a deterministic chart
selector. Spec §5.4 originally called for a third AI pass to propose chart
specs; that's now rendering/selector.py — a pure-code selector bound
directly to real dataframe columns, which makes a hallucinated field name
structurally impossible instead of merely unlikely. The AI's job is
editorial judgement (what's the story), not field-binding (which is exactly
the kind of thing code should own)."""
from rendering.selector import select_charts

from .pass_a_draft import draft_narrative
from .pass_c_verify import apply_verification, verify_narrative
from .pass_context import research_context


def run_pipeline(metadata: dict, profile: dict, insights: list[dict], df) -> dict:
    draft = draft_narrative(metadata, profile, insights)
    chart_specs = select_charts(insights, df)
    verification = verify_narrative(draft, profile, insights)
    verified_narrative = apply_verification(draft, verification)

    if not verified_narrative["observations"]:
        raise RuntimeError("all observations stripped by fact-verification — nothing left to publish")

    context = research_context(metadata, verified_narrative)
    if context:
        verified_narrative["why_it_matters"] = context["text"]
        verified_narrative["why_it_matters_sources"] = context["sources"]

    return {
        "narrative": verified_narrative,
        "chart_specs": chart_specs,
        "raw_draft": draft,
        "verification": verification,
        "insights": insights,
    }
