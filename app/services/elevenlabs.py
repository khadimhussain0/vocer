import secrets
import httpx
from app.config import get_settings


def _headers() -> dict:
    return {"xi-api-key": get_settings().elevenlabs_api_key}


def _base() -> str:
    return get_settings().elevenlabs_base_url


async def list_voices(client: httpx.AsyncClient) -> list[dict]:
    resp = await client.get(f"{_base()}/voices", headers=_headers())
    resp.raise_for_status()
    data = resp.json()
    return data.get("voices", [])


async def text_to_speech(
    client: httpx.AsyncClient,
    text: str,
    voice_id: str,
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
) -> bytes:
    url = f"{_base()}/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
        },
    }
    resp = await client.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.content


async def text_to_speech_stream(
    client: httpx.AsyncClient,
    text: str,
    voice_id: str,
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
):
    url = f"{_base()}/text-to-speech/{voice_id}/stream"
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
        },
    }
    async with client.stream("POST", url, json=payload, headers=_headers()) as resp:
        resp.raise_for_status()
        async for chunk in resp.aiter_bytes():
            yield chunk


async def speech_to_text(
    client: httpx.AsyncClient,
    audio_data: bytes,
    filename: str = "audio.wav",
) -> dict:
    url = f"{_base()}/speech-to-text"
    files = {"file": (filename, audio_data)}
    data = {"model_id": "scribe_v1", "timestamps_granularity": "word"}
    resp = await client.post(url, files=files, data=data, headers=_headers())
    resp.raise_for_status()
    return resp.json()


async def clone_voice(
    client: httpx.AsyncClient,
    name: str,
    files: list[tuple[str, bytes]],
    description: str = "",
) -> dict:
    url = f"{_base()}/voices/add"
    form_files = [("files", (fname, fdata)) for fname, fdata in files]
    data = {"name": name, "description": description}
    resp = await client.post(url, data=data, files=form_files, headers=_headers())
    resp.raise_for_status()
    return resp.json()


async def delete_voice(client: httpx.AsyncClient, voice_id: str) -> bool:
    url = f"{_base()}/voices/{voice_id}"
    resp = await client.delete(url, headers=_headers())
    resp.raise_for_status()
    return True


async def create_dubbing(
    client: httpx.AsyncClient,
    file_data: bytes,
    filename: str,
    source_lang: str,
    target_lang: str,
) -> dict:
    url = f"{_base()}/dubbing"
    files = {"file": (filename, file_data)}
    data = {
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
    resp = await client.post(url, data=data, files=files, headers=_headers())
    resp.raise_for_status()
    return resp.json()


async def get_dubbing_status(client: httpx.AsyncClient, dubbing_id: str) -> dict:
    url = f"{_base()}/dubbing/{dubbing_id}"
    resp = await client.get(url, headers=_headers())
    resp.raise_for_status()
    return resp.json()


async def get_dubbed_file(
    client: httpx.AsyncClient, dubbing_id: str, language_code: str
) -> bytes:
    url = f"{_base()}/dubbing/{dubbing_id}/audio/{language_code}"
    resp = await client.get(url, headers=_headers())
    resp.raise_for_status()
    return resp.content


async def create_agent(
    client: httpx.AsyncClient, voice_id: str = ""
) -> str:
    url = f"{_base()}/convai/agents/create"
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": "You are David, a professional and friendly sales agent at Vocer. Your job is to engage potential customers, understand their needs, present Vocer's voice AI products and services, handle objections with empathy, and guide them toward a purchase decision. Be conversational, persuasive but not pushy, ask qualifying questions, and always aim to provide value. Use a warm, confident tone.",
                },
                "first_message": "Hi, I'm David from the sales team at Vocer! Thanks for reaching out. I'd love to learn a bit about what you're looking for so I can help you find the perfect solution. What brings you in today?",
                "language": "en",
            },
            "tts": {
                "voice_id": voice_id or "pNInz6obpgDQGcFmaJgB",
            },
        },
        "name": "assistant_" + secrets.token_hex(4),
    }
    resp = await client.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()["agent_id"]


async def get_signed_url(client: httpx.AsyncClient, agent_id: str) -> str:
    url = f"{_base()}/convai/conversation/get-signed-url"
    resp = await client.get(
        url, params={"agent_id": agent_id}, headers=_headers()
    )
    resp.raise_for_status()
    return resp.json()["signed_url"]


async def generate_sound_effect(
    client: httpx.AsyncClient,
    text: str,
    duration_seconds: float = 5.0,
    prompt_influence: float = 0.3,
) -> bytes:
    url = f"{_base()}/sound-generation"
    payload = {
        "text": text,
        "duration_seconds": duration_seconds,
        "prompt_influence": prompt_influence,
    }
    resp = await client.post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.content
