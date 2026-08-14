from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict:
    return {"status": "ok"}


@app.get(settings.api_v1_prefix + "/ping")
async def ping() -> dict:
    return {"ping": "pong"}