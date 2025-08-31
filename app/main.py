from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

from app.dependencies import startup_client, shutdown_client
from app.routers import tts, stt, voices, translation, ws, sound_effects


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_client()
    yield
    await shutdown_client()


app = FastAPI(title="VOCER", version="1.0.0", lifespan=lifespan)

app.include_router(tts.router)
app.include_router(stt.router)
app.include_router(voices.router)
app.include_router(translation.router)
app.include_router(ws.router)
app.include_router(sound_effects.router)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")
