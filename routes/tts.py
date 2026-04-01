"""
Text-to-speech via ElevenLabs API.
"""

import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from models import User
from routes.auth import get_authenticated_user

router = APIRouter(tags=["TTS"])

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"


class TTSRequest(BaseModel):
    text: str
    voice_id: str = "EXAVITQu4vr4xnSDxMaL"


@router.post("/tts")
async def text_to_speech(
    body: TTSRequest,
    user: User = Depends(get_authenticated_user),
):
    """Convert text to speech via ElevenLabs. Returns audio/mpeg stream."""
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=503, detail="TTS not configured")

    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ELEVENLABS_URL}/{body.voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": body.text[:5000],
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"ElevenLabs error: {resp.text[:200]}",
            )

        return StreamingResponse(
            iter([resp.content]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline"},
        )
