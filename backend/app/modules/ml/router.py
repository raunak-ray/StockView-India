from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.modules.ml import capabilities as caps
from app.modules.ml import jobs, service
from app.modules.ml.schemas import (
    CapabilitiesResponse,
    EvalResponse,
    JobCreatedResponse,
    JobStatusResponse,
    LstmForecastResponse,
)

router = APIRouter(
    prefix="/ml",
    tags=["ml"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        **caps.capability_map(),
        active_ensemble=caps.active_ensemble(),
    )


@router.post("/predict", response_model=JobCreatedResponse, status_code=202)
async def start_predict(
    symbol: str = Query(..., min_length=1, max_length=32),
    use_lstm: bool = Query(False),
) -> JobCreatedResponse:
    clean = symbol.strip().upper()
    job_id = jobs.create_job(clean, service.predict(clean, use_lstm))
    return JobCreatedResponse(job_id=job_id, symbol=clean, status="running")


@router.get("/predict/{job_id}", response_model=JobStatusResponse)
async def get_predict(job_id: str) -> JobStatusResponse:
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown job id")
    return JobStatusResponse(**job)


@router.get("/lstm-forecast", response_model=LstmForecastResponse)
async def lstm_forecast(
    symbol: str = Query(..., min_length=1, max_length=32),
) -> LstmForecastResponse:
    clean = symbol.strip().upper()
    return LstmForecastResponse(**await service.lstm_forecast(clean))


@router.get("/eval", response_model=EvalResponse)
async def evaluate(
    symbol: str = Query(..., min_length=1, max_length=32),
) -> EvalResponse:
    clean = symbol.strip().upper()
    return EvalResponse(**await service.evaluate(clean))
