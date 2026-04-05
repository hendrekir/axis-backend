"""
OpenRouter service — single API for all model routing.

Routes triage and capture_classify through Gemini Flash 1.5 (cheap),
everything else through Claude Sonnet 4.6. Falls back to Claude on error.
"""

import logging
import os
import time

import httpx

logger = logging.getLogger("axis.openrouter")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Task type → OpenRouter model ID
TASK_MODEL_MAP = {
    "triage": "google/gemini-flash-1.5",
    "capture_classify": "google/gemini-flash-1.5",
    "dispatch": "anthropic/claude-sonnet-4-6",
    "draft_reply": "anthropic/claude-sonnet-4-6",
    "digest": "anthropic/claude-sonnet-4-6",
    "meeting_prep": "anthropic/claude-sonnet-4-6",
    "thread_response": "anthropic/claude-sonnet-4-6",
    "brain_dump": "anthropic/claude-sonnet-4-6",
    "research": "perplexity/sonar-online",
    "news": "perplexity/sonar-online",
    "discovery": "perplexity/sonar-online",
    "social": "x-ai/grok-beta",
    "entertainment": "x-ai/grok-beta",
}

FALLBACK_MODEL = "anthropic/claude-sonnet-4-6"


async def call_model(
    task: str,
    system: str,
    user_message: str,
    max_tokens: int = 1024,
) -> dict:
    """Route a prompt through OpenRouter to the right model.

    Args:
        task: Task type key (e.g. "triage", "dispatch", "draft_reply").
        system: System prompt.
        user_message: User message content.
        max_tokens: Max response tokens.

    Returns:
        {"text": str, "model": str, "elapsed_ms": int}
    """
    if not OPENROUTER_API_KEY:
        # Fall back to direct Anthropic SDK if no OpenRouter key
        logger.warning("OPENROUTER_API_KEY not set — falling back to direct Anthropic")
        from services.claude_service import generate
        start = time.monotonic()
        text = await generate(system_prompt=system, user_message=user_message, max_tokens=max_tokens)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return {"text": text, "model": "claude-direct", "elapsed_ms": elapsed_ms}

    model = TASK_MODEL_MAP.get(task, FALLBACK_MODEL)
    start = time.monotonic()

    try:
        text = await _openrouter_chat(model, system, user_message, max_tokens)
    except Exception as e:
        logger.warning("OpenRouter %s failed for task=%s: %s — falling back to %s", model, task, e, FALLBACK_MODEL)
        if model != FALLBACK_MODEL:
            text = await _openrouter_chat(FALLBACK_MODEL, system, user_message, max_tokens)
            model = FALLBACK_MODEL
        else:
            raise

    elapsed_ms = int((time.monotonic() - start) * 1000)
    logger.info("OpenRouter task=%s model=%s %dms", task, model, elapsed_ms)
    return {"text": text, "model": model, "elapsed_ms": elapsed_ms}


async def _openrouter_chat(
    model: str, system: str, user_message: str, max_tokens: int
) -> str:
    """Call the OpenRouter chat completions endpoint."""
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://tryaxis.app",
                "X-Title": "Axis",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
