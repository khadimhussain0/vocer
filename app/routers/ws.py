import json
import asyncio
import base64
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.config import get_settings
from app.dependencies import get_client
from app.services import elevenlabs

router = APIRouter(tags=["websocket"])

ELEVENLABS_STT_WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
MYMEMORY_URL = "https://api.mymemory.translated.net/get"


def _build_stt_url(language_code: str = "en") -> str:
    return (
        f"{ELEVENLABS_STT_WS_URL}"
        f"?model_id=scribe_v2_realtime"
        f"&language_code={language_code}"
        f"&audio_format=pcm_16000"
        f"&commit_strategy=vad"
    )


@router.websocket("/ws/stt")
async def live_stt(ws: WebSocket):
    await ws.accept()

    settings = get_settings()
    api_key = settings.elevenlabs_api_key

    stt_url = _build_stt_url("en")

    try:
        async with websockets.connect(
            stt_url,
            additional_headers={"xi-api-key": api_key},
        ) as el_ws:

            async def forward_audio():
                try:
                    while True:
                        data = await ws.receive_text()
                        msg = json.loads(data)
                        if msg.get("type") == "audio":
                            audio_msg = {
                                "message_type": "input_audio_chunk",
                                "audio_base_64": msg["audio"],
                                "sample_rate": 16000,
                            }
                            await el_ws.send(json.dumps(audio_msg))
                        elif msg.get("type") == "stop":
                            await el_ws.send(
                                json.dumps({"message_type": "flush"})
                            )
                except WebSocketDisconnect:
                    try:
                        await el_ws.send(
                            json.dumps({"message_type": "flush"})
                        )
                    except Exception:
                        pass

            async def forward_transcript():
                try:
                    async for message in el_ws:
                        data = json.loads(message)
                        mt = data.get("message_type", "")
                        if mt == "partial_transcript":
                            await ws.send_json(
                                {"type": "transcript", "text": data.get("text", "")}
                            )
                        elif mt in ("committed_transcript", "committed_transcript_with_timestamps"):
                            await ws.send_json(
                                {"type": "final_transcript", "text": data.get("text", "")}
                            )
                except Exception:
                    pass

            await asyncio.gather(forward_audio(), forward_transcript())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@router.websocket("/ws/translate")
async def live_translate(ws: WebSocket):
    await ws.accept()

    settings = get_settings()
    api_key = settings.elevenlabs_api_key
    client = get_client()

    try:
        config_data = await ws.receive_text()
        config = json.loads(config_data)
        source_lang = config.get("source_lang", "en")
        target_lang = config.get("target_lang", "es")
        voice_id = config.get("voice_id", "")
    except Exception:
        source_lang, target_lang, voice_id = "en", "es", ""

    stt_url = _build_stt_url(source_lang)

    try:
        async with websockets.connect(
            stt_url,
            additional_headers={"xi-api-key": api_key},
        ) as el_ws:

            async def forward_audio():
                try:
                    while True:
                        data = await ws.receive_text()
                        msg = json.loads(data)
                        if msg.get("type") == "audio":
                            await el_ws.send(
                                json.dumps(
                                    {
                                        "message_type": "input_audio_chunk",
                                        "audio_base_64": msg["audio"],
                                        "sample_rate": 16000,
                                    }
                                )
                            )
                        elif msg.get("type") == "stop":
                            await el_ws.send(
                                json.dumps({"message_type": "flush"})
                            )
                except WebSocketDisconnect:
                    try:
                        await el_ws.send(
                            json.dumps({"message_type": "flush"})
                        )
                    except Exception:
                        pass

            async def forward_translate():
                try:
                    async for message in el_ws:
                        data = json.loads(message)
                        mt = data.get("message_type", "")

                        if mt == "partial_transcript":
                            await ws.send_json(
                                {
                                    "type": "partial",
                                    "text": data.get("text", ""),
                                }
                            )
                        elif mt in ("committed_transcript", "committed_transcript_with_timestamps"):
                            text = data.get("text", "").strip()
                            if not text:
                                continue
                            await ws.send_json(
                                {"type": "source", "text": text}
                            )
                            langpair = f"{source_lang}|{target_lang}"
                            try:
                                resp = await client.get(
                                    MYMEMORY_URL,
                                    params={"q": text, "langpair": langpair},
                                )
                                resp.raise_for_status()
                                translated = (
                                    resp.json()
                                    .get("responseData", {})
                                    .get("translatedText", "")
                                )
                                await ws.send_json(
                                    {
                                        "type": "translation",
                                        "text": translated,
                                    }
                                )
                                if voice_id:
                                    audio = await elevenlabs.text_to_speech(
                                        client,
                                        text=translated,
                                        voice_id=voice_id,
                                    )
                                    await ws.send_json(
                                        {
                                            "type": "audio",
                                            "audio": base64.b64encode(
                                                audio
                                            ).decode(),
                                        }
                                    )
                            except Exception as e:
                                await ws.send_json(
                                    {
                                        "type": "error",
                                        "message": f"Translation error: {e}",
                                    }
                                )
                except Exception:
                    pass

            await asyncio.gather(forward_audio(), forward_translate())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@router.websocket("/ws/conversation")
async def live_conversation(ws: WebSocket):
    await ws.accept()

    settings = get_settings()
    client = get_client()

    voice_id = ""
    try:
        config_data = await ws.receive_text()
        config = json.loads(config_data)
        agent_id = config.get("agent_id", "") or settings.elevenlabs_agent_id
        voice_id = config.get("voice_id", "")
    except Exception:
        agent_id = settings.elevenlabs_agent_id

    if not agent_id:
        try:
            await ws.send_json({"type": "status", "message": "Creating AI agent..."})
            agent_id = await elevenlabs.create_agent(client, voice_id=voice_id)
        except Exception as e:
            await ws.send_json({"type": "error", "message": f"Failed to create agent: {e}"})
            await ws.close()
            return

    try:
        signed_url = await elevenlabs.get_signed_url(client, agent_id)
    except Exception as e:
        await ws.send_json({"type": "error", "message": f"Failed to get signed URL: {e}"})
        await ws.close()
        return

    try:
        async with websockets.connect(signed_url) as el_ws:

            async def forward_audio():
                try:
                    while True:
                        data = await ws.receive_text()
                        msg = json.loads(data)
                        if msg.get("type") == "audio":
                            await el_ws.send(
                                json.dumps({
                                    "user_audio_chunk": msg["audio"],
                                })
                            )
                        elif msg.get("type") == "stop":
                            break
                except WebSocketDisconnect:
                    pass

            async def forward_responses():
                try:
                    async for message in el_ws:
                        data = json.loads(message)
                        msg_type = data.get("type", "")

                        if msg_type == "conversation_initiation_metadata":
                            meta = data.get("conversation_initiation_metadata_event", {})
                            await ws.send_json({
                                "type": "connected",
                                "conversation_id": meta.get("conversation_id", ""),
                                "output_format": meta.get("agent_output_audio_format", "pcm_16000"),
                            })
                        elif msg_type == "audio":
                            audio_event = data.get("audio_event", {})
                            await ws.send_json({
                                "type": "audio",
                                "audio": audio_event.get("audio_base_64", ""),
                                "event_id": audio_event.get("event_id"),
                            })
                        elif msg_type == "agent_response":
                            await ws.send_json({
                                "type": "agent_transcript",
                                "text": data.get("agent_response_event", {}).get("agent_response", ""),
                            })
                        elif msg_type == "user_transcript":
                            await ws.send_json({
                                "type": "user_transcript",
                                "text": data.get("user_transcription_event", {}).get("user_transcript", ""),
                            })
                        elif msg_type == "interruption":
                            await ws.send_json({"type": "interruption"})
                        elif msg_type == "ping":
                            await el_ws.send(json.dumps({
                                "type": "pong",
                                "event_id": data.get("ping_event", {}).get("event_id"),
                            }))
                except Exception:
                    pass

            await asyncio.gather(forward_audio(), forward_responses())

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass
