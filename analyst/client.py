"""Shared Claude call helper — forces structured JSON output via tool use,
since Pass C in particular must be programmatically checkable (spec §5.4/§12).
"""
import json

import anthropic

from config import ANALYST_MODEL, ANTHROPIC_API_KEY

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY not set — see .env.example")
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def call_structured(system: str, user_content: str, tool_name: str, tool_schema: dict) -> dict:
    """One Claude call, forced to respond via a single tool call matching
    tool_schema. Returns the parsed tool input dict."""
    client = _get_client()
    resp = client.messages.create(
        model=ANALYST_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
        tools=[{"name": tool_name, "description": f"Submit {tool_name}", "input_schema": tool_schema}],
        tool_choice={"type": "tool", "name": tool_name},
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise RuntimeError(f"Claude did not return a {tool_name} tool call: {resp.content}")
