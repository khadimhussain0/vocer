from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from app.dependencies import get_client
from app.services import elevenlabs

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0


@router.post("")
async def text_to_speech(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(400, "Text is required")
    client = get_client()
    audio = await elevenlabs.text_to_speech(
        client,
        text=req.text,
        voice_id=req.voice_id,
        model_id=req.model_id,
        stability=req.stability,
        similarity_boost=req.similarity_boost,
        style=req.style,
    )
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/stream")
async def text_to_speech_stream(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(400, "Text is required")
    client = get_client()
    return StreamingResponse(
        elevenlabs.text_to_speech_stream(
            client,
            text=req.text,
            voice_id=req.voice_id,
            model_id=req.model_id,
            stability=req.stability,
            similarity_boost=req.similarity_boost,
            style=req.style,
        ),
        media_type="audio/mpeg",
    )
