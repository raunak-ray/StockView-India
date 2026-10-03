import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.db import SessionLocal, init_db, ping_db
from app.core.news_db import close_news_db, init_news_db, ping_news_db
from app.core.redis import close_redis
from app.modules.alerts.router import alerts_router
from app.modules.analytics.router import router as analytics_router
from app.modules.auth import service
from app.modules.auth.router import router as auth_router
from app.modules.backtesting.router import router as backtesting_router
from app.modules.blockchain.router import router as blockchain_router
from app.modules.compare.router import compare_router
from app.modules.instruments.router import router as instruments_router
from app.modules.market_data.router import router as market_data_router
from app.modules.ml.router import router as ml_router
from app.modules.news.router import router as news_router
from app.modules.nse.router import router as nse_router
from app.modules.portfolio.router import router as portfolio_router
from app.modules.sentiment.router import router as sentiment_router
from app.modules.signals.router import router as signals_router
from app.modules.smc.router import router as smc_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with SessionLocal() as db:
        await service.seed_users(db)
    # News DB is best-effort: if it is unreachable the app must still boot, so
    # /news endpoints fail with 502 while everything else keeps working.
    try:
        await init_news_db()
    except SQLAlchemyError:
        logger.warning("news database unavailable — /news endpoints will 502", exc_info=True)
    yield
    await close_news_db()
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
    app.include_router(nse_router, prefix=settings.api_v1_prefix)
    app.include_router(sentiment_router, prefix=settings.api_v1_prefix)
    app.include_router(ml_router, prefix=settings.api_v1_prefix)
    app.include_router(alerts_router, prefix=settings.api_v1_prefix)
    app.include_router(compare_router, prefix=settings.api_v1_prefix)
    app.include_router(backtesting_router, prefix=settings.api_v1_prefix)
    app.include_router(blockchain_router, prefix=settings.api_v1_prefix)
    app.include_router(news_router, prefix=settings.api_v1_prefix)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz", response_model=None)
    async def readyz() -> dict | JSONResponse:
        """Ready probe. `db_unreachable` fails; a dead news DB only degrades
        /news, so it is reported but does not fail the probe."""
        try:
            await ping_db()
        except (SQLAlchemyError, OSError):
            return JSONResponse(status_code=503, content={"status": "db_unreachable"})

        news_status = "ok"
        try:
            await ping_news_db()
        except (SQLAlchemyError, OSError):
            news_status = "unreachable"

        return {"status": "ok", "news_db": news_status}

    @app.get(settings.api_v1_prefix + "/ping")
    async def ping() -> dict:
        return {"ping": "pong"}

    return app


app = create_app()