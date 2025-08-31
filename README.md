# VOCER - Voice AI Studio

A full-featured voice AI web application powered by ElevenLabs, built with FastAPI and Tailwind CSS. Features a real-time **AI voice agent** alongside speech-to-text, text-to-speech, translation, and sound effects — all in a polished dark glassmorphism UI.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

| Feature | Description |
|---------|-------------|
| **AI Agent** | Real-time voice conversation with an AI sales agent via ElevenLabs Conversational AI. Auto-creates agents with configurable voice. |
| **Speech to Text** | Upload files, record from mic, or use real-time live transcription. Word-level timestamps, SRT export. |
| **Text to Speech** | Voice selector, model toggle, stability/clarity/style sliders, audio download. |
| **Voice Cloning** | Upload audio samples to create custom voice clones usable across TTS features. |
| **Translation** | Text translation, audio/video dubbing, and live mic-to-translation with spoken output. |
| **Sound Effects** | Generate sound effects from text descriptions with adjustable duration and influence. |

## Tech Stack

- **Backend:** FastAPI + httpx (async HTTP)
- **Frontend:** Single HTML file, Tailwind CSS CDN, vanilla JS
- **Real-time:** WebSocket proxy (FastAPI <-> ElevenLabs WebSocket)
- **APIs:** ElevenLabs (TTS, STT, cloning, dubbing), MyMemory (translation)
- **Container:** Docker + docker-compose

## Quick Start

### Prerequisites

- Docker and docker-compose
- An [ElevenLabs](https://elevenlabs.io) API key

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/vocer.git
   cd vocer
   ```

2. Create a `.env` file in the project root with your ElevenLabs API key:
   ```
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ELEVENLABS_AGENT_ID=your_agent_id_here  # optional, for AI Agent feature
   ```
   You can get one at [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys).

3. Start the application:
   ```bash
   docker compose up --build
   ```

4. Open http://localhost:8000

### Run Without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

> **Note:** The `.env` file must exist in the project root with `ELEVENLABS_API_KEY` set, regardless of how you run the app. `ELEVENLABS_AGENT_ID` is optional — if not set, the AI Agent feature will create one automatically via the API.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the SPA |
| `GET` | `/api/voices` | List available voices |
| `POST` | `/api/voices/clone` | Create a voice clone |
| `DELETE` | `/api/voices/{id}` | Delete a voice |
| `POST` | `/api/tts` | Text to speech |
| `POST` | `/api/tts/stream` | Streaming text to speech |
| `POST` | `/api/stt` | Speech to text (file upload) |
| `POST` | `/api/translate/text` | Translate text |
| `POST` | `/api/translate/audio` | Start audio dubbing |
| `GET` | `/api/translate/audio/{id}/status` | Dubbing status |
| `GET` | `/api/translate/audio/{id}/download/{lang}` | Download dubbed audio |
| `POST` | `/api/sound-effects` | Generate sound effects from text |
| `WS` | `/ws/stt` | Live speech to text |
| `WS` | `/ws/translate` | Live translation |
| `WS` | `/ws/conversation` | AI agent voice conversation |

## License

MIT
