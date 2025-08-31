from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.dependencies import get_client
from app.services import elevenlabs

router = APIRouter(prefix="/api/voices", tags=["voices"])


@router.get("")
async def list_voices():
    client = get_client()
    voices = await elevenlabs.list_voices(client)
    return {"voices": voices}


@router.post("/clone")
async def clone_voice(
    name: str = Form(...),
    description: str = Form(""),
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(400, "At least one audio file is required")
    file_data = []
    for f in files:
        data = await f.read()
        file_data.append((f.filename or "sample.mp3", data))
    client = get_client()
    result = await elevenlabs.clone_voice(client, name, file_data, description)
    return result


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    client = get_client()
    await elevenlabs.delete_voice(client, voice_id)
    return {"status": "deleted"}
