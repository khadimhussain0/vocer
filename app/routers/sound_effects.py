from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.dependencies import get_client
from app.services import elevenlabs

router = APIRouter(prefix="/api", tags=["sound-effects"])


class SoundEffectRequest(BaseModel):
    text: str
    duration_seconds: float = Field(default=5.0, ge=0.5, le=30.0)
    prompt_influence: float = Field(default=0.3, ge=0.0, le=1.0)


@router.post("/sound-effects")
async def generate_sound_effect(req: SoundEffectRequest):
    client = get_client()
    audio = await elevenlabs.generate_sound_effect(
        client,
        text=req.text,
        duration_seconds=req.duration_seconds,
        prompt_influence=req.prompt_influence,
    )
    return Response(content=audio, media_type="audio/mpeg")
