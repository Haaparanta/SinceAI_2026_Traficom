"""One Claude client for the whole backend (pm_pack/06 "LLM contract").

* Model from LLM_MODEL, default claude-opus-5-5; adaptive thinking (always on for this model), effort per call.
* Output is JSON constrained by a schema (output_config.format) and validated with Pydantic before use.
* Server-side refusal fallback is on (betas server-side-fallback-2026-07-01, fallbacks="default"), so a safety
  decline is retried on another model inside the same call instead of failing the demo; the final stop_reason is
  still checked before the content is read.
* LLM_DISABLED=1, or no credentials, means no call is made: callers fall back to their deterministic template.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from radar.config import settings

T = TypeVar("T", bound=BaseModel)
FALLBACK_BETA = "server-side-fallback-2026-07-01"
_client = None


class LLMUnavailable(RuntimeError):
    """No call was made (disabled or no credentials)."""


class LLMRefused(RuntimeError):
    """The model chain declined (stop_reason refusal) or stopped early."""


@dataclass
class LLMResult:
    output: BaseModel
    model: str
    stop_reason: str
    fallback_used: bool
    input_tokens: int
    output_tokens: int


def credentials_present() -> bool:
    """API key, auth token, or a profile from `ant auth login` (the SDK reads all three)."""
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    return (Path.home() / ".config" / "anthropic").exists()


def status() -> dict:
    if os.environ.get("LLM_DISABLED", "1" if settings.llm_disabled else "0") == "1":
        return {"available": False, "model": settings.llm_model, "reason": "LLM_DISABLED=1"}
    if not credentials_present():
        return {"available": False, "model": settings.llm_model,
                "reason": "no Claude API credentials (set ANTHROPIC_API_KEY or run `ant auth login`)"}
    return {"available": True, "model": settings.llm_model, "reason": ""}


def get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic()
    return _client


def _schema(model: type[BaseModel]) -> dict:
    """Pydantic JSON schema tightened for structured outputs: closed objects, every property required."""
    s = model.model_json_schema()
    s["additionalProperties"] = False
    s["required"] = list(s.get("properties", {}))
    return s


def generate(system: str, user: str, output: type[T], *, effort: str, max_tokens: int, client=None) -> LLMResult:
    st = status()
    if client is None and not st["available"]:
        raise LLMUnavailable(st["reason"])
    c = client or get_client()
    response = c.beta.messages.create(
        model=os.environ.get("LLM_MODEL", settings.llm_model),
        max_tokens=max_tokens,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": _schema(output)}},
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        category = getattr(getattr(response, "stop_details", None), "category", None)
        raise LLMRefused(f"the model declined (category {category})")
    if response.stop_reason != "end_turn":
        raise LLMRefused(f"the model stopped early (stop_reason {response.stop_reason})")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise LLMRefused("no text block in the response")
    parsed = output.model_validate(json.loads(text))
    iterations = getattr(response.usage, "iterations", None) or []
    return LLMResult(
        output=parsed, model=response.model, stop_reason=response.stop_reason,
        fallback_used=any(getattr(i, "type", "") == "fallback_message" for i in iterations),
        input_tokens=response.usage.input_tokens, output_tokens=response.usage.output_tokens,
    )
