"""
Multi-model routing — sends prompts to the right AI model based on task type.

Supports: Claude (default), Perplexity, Grok, Gemini Flash-Lite, Gemini Pro, GPT-5.
Falls back to Claude if a model's API key is not configured.
"""

import logging
import os
import time

import httpx

from services.claude_service import generate as claude_generate

logger = logging.getLogger("axis.model_router")

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Task type → model mapping (matches AXIS_INTELLIGENCE_v1.md routing tree)
DEFAULT_ROUTES = {
    "email_draft": "claude",
    "thread_response": "claude",
    "morning_digest": "claude",
    "meeting_prep": "claude",
    "brain_dump": "claude",
    "research": "perplexity",
    "news": "perplexity",
    "person_lookup": "perplexity",
    "current_events": "perplexity",
    "entertainment": "grok",
    "social_trends": "grok",
    "sports": "grok",
    "music": "grok",
    "triage": "gemini_flash",
    "youtube_summary": "gemini_flash",
    "image_analysis": "gemini_flash",
    "complex_reasoning": "gemini_pro",
    "code_execution": "gpt5",
    "data_analysis": "gpt5",
}


def resolve_model(task_type: str, override: str | None = None) -> str:
    """Determine which model to use. Override takes priority, then DEFAULT_ROUTES, then claude."""
    if override:
        return override
    return DEFAULT_ROUTES.get(task_type, "claude")


async def route(
    task_type: str,
    system: str,
    user_msg: str,
    model_override: str | None = None,
    max_tokens: int = 1024,
) -> dict:
    """Route a prompt to the right model. Returns { text, model, elapsed_ms }."""
    model = resolve_model(task_type, model_override)
    start = time.monotonic()

    try:
        text = await _call_model(model, system, user_msg, max_tokens)
    except Exception as e:
        logger.warning("Model %s failed for task %s: %s — falling back to Claude", model, task_type, e)
        model = "claude"
        text = await _call_model("claude", system, user_msg, max_tokens)

    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.info("Routed task_type=%s to model=%s in %dms", task_type, model, elapsed_ms)
    return {"text": text, "model": model, "elapsed_ms": elapsed_ms}


async def _call_model(model: str, system: str, user_msg: str, max_tokens: int) -> str:
    """Dispatch to the correct model API."""
    if model == "perplexity":
        return await _call_perplexity(system, user_msg)
    elif model == "grok":
        return await _call_grok(system, user_msg)
    elif model == "gemini_flash":
        return await _call_gemini(system, user_msg, "gemini-2.0-flash-lite")
    elif model == "gemini_pro":
        return await _call_gemini(system, user_msg, "gemini-2.0-pro")
    elif model == "gpt5":
        return await _call_openai(system, user_msg, max_tokens)
    else:
        return await claude_generate(system_prompt=system, user_message=user_msg, max_tokens=max_tokens)


async def _call_openai_compatible(
    base_url: str, api_key: str, model_name: str, system: str, user_msg: str
) -> str:
    """Generic caller for OpenAI-compatible chat APIs (Perplexity, Grok, OpenAI)."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_perplexity(system: str, user_msg: str) -> str:
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY not configured")
    return await _call_openai_compatible(
        "https://api.perplexity.ai", PERPLEXITY_API_KEY,
        "sonar-pro", system, user_msg,
    )


async def _call_grok(system: str, user_msg: str) -> str:
    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY not configured")
    return await _call_openai_compatible(
        "https://api.x.ai/v1", GROK_API_KEY,
        "grok-3-fast", system, user_msg,
    )


async def _call_openai(system: str, user_msg: str, max_tokens: int) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    return await _call_openai_compatible(
        "https://api.openai.com/v1", OPENAI_API_KEY,
        "gpt-4o", system, user_msg,
    )


async def _call_gemini(system: str, user_msg: str, model_name: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": f"{system}\n\n{user_msg}"}]}],
            },
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
