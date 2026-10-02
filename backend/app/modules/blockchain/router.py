from collections.abc import Callable, Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException
from starlette.concurrency import run_in_threadpool

from app.core.deps import get_current_user
from app.modules.blockchain import service
from app.modules.blockchain.schemas import (
    BlockchainAutoSaveRequest,
    BlockchainAutoSaveResponse,
    BlockchainLatestPredictionResponse,
    BlockchainPredictionRequest,
    BlockchainPredictionResponse,
    BlockchainStatusResponse,
)

router = APIRouter(
    prefix="/blockchain",
    tags=["blockchain"],
    dependencies=[Depends(get_current_user)],
)


@contextmanager
def _map_chain_errors() -> Iterator[None]:
    """Turn raw web3/connection failures into clean HTTP responses."""

    try:
        yield
    except HTTPException:
        raise
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Blockchain call failed: {exc}",
        ) from exc


async def _run_chain[T](fn: Callable[[], T]) -> T:
    """Run a blocking web3 call off the event loop."""

    with _map_chain_errors():
        return await run_in_threadpool(fn)


@router.post(
    "/predictions",
    response_model=BlockchainPredictionResponse,
)
async def save_prediction(
    payload: BlockchainPredictionRequest,
) -> BlockchainPredictionResponse:

    result = await _run_chain(
        lambda: service.store_prediction(
            stock_name=payload.stock_name,
            current_price=payload.current_price,
            predicted_price=payload.predicted_price,
            direction=payload.direction,
            confidence=payload.confidence,
            up_probability=payload.up_probability,
            down_probability=payload.down_probability,
            signal_score=payload.signal_score,
            stop_loss=payload.stop_loss,
            target_price=payload.target_price,
        )
    )

    return BlockchainPredictionResponse(**result)


@router.get(
    "/predictions/latest",
    response_model=BlockchainLatestPredictionResponse,
)
async def latest_prediction() -> BlockchainLatestPredictionResponse:

    result = await _run_chain(service.get_latest_prediction)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No blockchain predictions found.",
        )

    return BlockchainLatestPredictionResponse(**result)


@router.post(
    "/predictions/auto",
    response_model=BlockchainAutoSaveResponse,
)
async def auto_save_prediction(
    payload: BlockchainAutoSaveRequest,
) -> BlockchainAutoSaveResponse:

    with _map_chain_errors():
        result = await service.store_prediction_from_stockview(
            payload.symbol
        )

    return BlockchainAutoSaveResponse(**result)


@router.get(
    "/status",
    response_model=BlockchainStatusResponse,
)
async def blockchain_status() -> BlockchainStatusResponse:

    result = await _run_chain(service.get_blockchain_status)

    return BlockchainStatusResponse(**result)
