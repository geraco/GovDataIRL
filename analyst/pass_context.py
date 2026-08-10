"""Optional context pass — uses Claude's server-side web_search tool to find
real-world relevance (news, debate, commentary) for the headline finding.
Best-effort and non-fatal: if search finds nothing relevant, or the call
fails for any reason, the report still publishes without this section
(spec §10's resilience principle — a missing enhancement is not a failure).

Deliberately NOT fact-checked by Pass C: these are external claims about the
world, not claims about the dataset, and must read as attributed reporting/
commentary rather than verified statistics — the prompt below enforces that
distinction explicitly.
"""
from config import ANALYST_MODEL, ANTHROPIC_API_KEY
from .client import _get_client

SYSTEM_PROMPT = """You are researching real-world context for a short Irish data-journalism
piece. You will be given the piece's headline finding and dataset topic.

Use web search to find recent, genuinely relevant Irish news coverage, public
debate, or commentary connected to this specific finding or topic — not just
the general subject area.

Write a short "why this matters" note (2-3 sentences, plain language) for a
general reader explaining the real-world relevance of this finding. If you
find genuinely relevant coverage, ground the note in it and you may
reference what was reported (e.g. "this follows..."). If nothing you find is
genuinely and specifically relevant, do not force a connection — instead
write 1-2 sentences on the topic's general real-world relevance based on
what the dataset itself covers, and do not claim to have found related
coverage.

Critical rule: anything you state that comes from a web search is your
research, not a verified statistic from the dataset — do not present it with
the same certainty as the dataset's own numbers, and do not invent numbers
of your own. Keep the whole note under 60 words.

Output format: respond with ONLY the finished note itself, as plain prose.
No preamble ("Based on my search..."), no restating your instructions, no
markdown formatting, no heading or label — the note is inserted directly
under a "Why this matters" heading that already exists in the page."""


def research_context(metadata: dict, narrative: dict) -> dict | None:
    if not ANTHROPIC_API_KEY:
        return None
    try:
        client = _get_client()
        user_content = (
            f"Headline finding: {narrative['headline']}\n"
            f"Dataset topic: {metadata['title']} (publisher: {metadata['publisher']})\n"
            f"Description: {metadata.get('description', '')[:500]}"
        )
        resp = client.messages.create(
            model=ANALYST_MODEL, max_tokens=600,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
            messages=[{"role": "user", "content": user_content}],
        )
    except Exception:
        return None  # web search unavailable/failed — the report still publishes without it

    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not text:
        return None

    sources = []
    seen = set()
    for block in resp.content:
        if block.type != "text":
            continue
        for citation in getattr(block, "citations", None) or []:
            url = getattr(citation, "url", None)
            title = getattr(citation, "title", None)
            if url and url not in seen:
                seen.add(url)
                sources.append({"url": url, "title": title or url})

    return {"text": text, "sources": sources[:3]}
