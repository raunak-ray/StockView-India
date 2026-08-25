from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.modules.alerts.schemas import AlertCheckResult, AlertCreate, AlertOut
from app.modules.alerts.service import (
    add_alert,
    check_alerts,
    clear_all,
    clear_triggered,
    delete_alert,
    get_user_alerts,
)
from app.modules.auth.models import User

alerts_router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
    dependencies=[Depends(get_current_user)],
)


@alerts_router.get("", response_model=AlertCheckResult)
async def list_alerts(user: User = Depends(get_current_user)) -> AlertCheckResult:
    triggered_now = await check_alerts(str(user.id))
    all_alerts = get_user_alerts(str(user.id))
    active = [AlertOut.model_validate(a.__dict__) for a in all_alerts if not a.triggered]
    fired = [AlertOut.model_validate(a.__dict__) for a in all_alerts if a.triggered]
    return AlertCheckResult(
        triggered_now=[AlertOut.model_validate(a.__dict__) for a in triggered_now],
        active=active,
        fired=fired,
    )


@alerts_router.post("", response_model=AlertOut, status_code=201)
async def create_alert(
    body: AlertCreate,
    user: User = Depends(get_current_user),
) -> AlertOut:
    alert = add_alert(
        str(user.id),
        symbol=body.symbol.upper(),
        price=body.price,
        condition=body.condition,
        label=body.label,
    )
    if alert is None:
        raise HTTPException(409, "Alert already exists")
    return AlertOut.model_validate(alert.__dict__)


@alerts_router.delete("/{alert_id}", status_code=204)
async def remove_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
) -> None:
    if not delete_alert(str(user.id), alert_id):
        raise HTTPException(404, "Alert not found")


@alerts_router.delete("", status_code=204)
async def clear(
    fired_only: bool = False,
    user: User = Depends(get_current_user),
) -> None:
    if fired_only:
        clear_triggered(str(user.id))
    else:
        clear_all(str(user.id))
