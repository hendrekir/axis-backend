from dotenv import load_dotenv
load_dotenv()

import os
import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY is empty — check your .env file")
else:
    print(f"Anthropic key loaded: {ANTHROPIC_API_KEY[:12]}...{ANTHROPIC_API_KEY[-4:]}")

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-5"


async def generate(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """Send a message to Claude and return the text response."""
    response = await client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


async def chat(system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> str:
    """Send a multi-turn conversation to Claude and return the text response."""
    response = await client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text
