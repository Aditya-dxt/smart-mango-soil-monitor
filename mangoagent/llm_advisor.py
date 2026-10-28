"""Optional LLM layer: turns a Decision into a plain-language note for the farmer.

It never controls the valve. If no API key is configured or the call fails, the agent
falls back to its built-in template explanation. (Not exercised in the automated
tests because it needs network access and an API key.)
"""
from __future__ import annotations
import json, os


def make_advisor(model: str | None = None, language: str = "English"):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic(api_key=key)
    model = model or os.getenv("ADVISOR_MODEL", "claude-sonnet-5-5")

    def explain(decision) -> str:
        msg = client.messages.create(
            model=model, max_tokens=250,
            system=("You assist a mango farmer. In 2-3 short sentences in "
                    f"{language}, explain the irrigation decision and any alerts. "
                    "Use only the facts given. Do not invent numbers or change the decision."),
            messages=[{"role": "user", "content": json.dumps(decision.to_dict())}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()

    return explain
