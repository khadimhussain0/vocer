import base64
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from app.dependencies import get_client
from app.services import elevenlabs

router = APIRouter(prefix="/api/translate", tags=["translation"])

MYMEMORY_URL = "https://api.mymemory.translated.net/get"


class TextTranslateRequest(BaseModel):
    text: str
    source_lang: str = "en"
    target_lang: str = "es"
    voice_id: str = ""
    speak: bool = False


@router.post("/text")
async def translate_text(req: TextTranslateRequest):
    if not req.text.strip():
        raise HTTPException(400, "Text is required")

    client = get_client()

    langpair = f"{req.source_lang}|{req.target_lang}"
    resp = await client.get(
        MYMEMORY_URL, params={"q": req.text, "langpair": langpair}
    )
    resp.raise_for_status()
    data = resp.json()
    translated = data.get("responseData", {}).get("translatedText", "")

    result = {"translated_text": translated, "source_text": req.text}

    if req.speak and req.voice_id:
        audio = await elevenlabs.text_to_speech(
            client, text=translated, voice_id=req.voice_id
        )
        result["audio_base64"] = base64.b64encode(audio).decode()

    return result


@router.post("/audio")
async def translate_audio(
    file: UploadFile = File(...),
    source_lang: str = Form("en"),
    target_lang: str = Form("es"),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    client = get_client()
    result = await elevenlabs.create_dubbing(
        client, data, file.filename or "audio.mp3", source_lang, target_lang
    )
    return result


@router.get("/audio/{dubbing_id}/status")
async def dubbing_status(dubbing_id: str):
    client = get_client()
    return await elevenlabs.get_dubbing_status(client, dubbing_id)


@router.get("/audio/{dubbing_id}/download/{language_code}")
async def download_dubbed(dubbing_id: str, language_code: str):
    client = get_client()
    audio = await elevenlabs.get_dubbed_file(client, dubbing_id, language_code)
    return Response(content=audio, media_type="audio/mpeg")
