from fastapi import APIRouter, UploadFile, File, HTTPException
from app.dependencies import get_client
from app.services import elevenlabs

router = APIRouter(prefix="/api/stt", tags=["stt"])


@router.post("")
async def speech_to_text(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    client = get_client()
    result = await elevenlabs.speech_to_text(client, data, file.filename)
    return result
