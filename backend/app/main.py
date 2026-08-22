from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.redis import close_redis
from app.modules.analytics.router import router as analytics_router
from app.modules.auth import service
from app.modules.auth.router import router as auth_router
from app.modules.instruments.router import router as instruments_router
from app.modules.market_data.router import router as market_data_router
from app.modules.portfolio.router import router as portfolio_router
from app.modules.signals.router import router as signals_router
from app.modules.smc.router import router as smc_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with SessionLocal() as db:
        await service.seed_users(db)
    yield
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(instruments_router, prefix=settings.api_v1_prefix)
    app.include_router(market_data_router, prefix=settings.api_v1_prefix)
    app.include_router(portfolio_router, prefix=settings.api_v1_prefix)
    app.include_router(analytics_router, prefix=settings.api_v1_prefix)
    app.include_router(signals_router, prefix=settings.api_v1_prefix)
    app.include_router(smc_router, prefix=settings.api_v1_prefix)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict:
        return {"status": "ok"}

    @app.get(settings.api_v1_prefix + "/ping")
    async def ping() -> dict:
        return {"ping": "pong"}

    return app


app = create_app()