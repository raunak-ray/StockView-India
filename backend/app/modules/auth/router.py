from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import check_rate_limit, get_client_ip, get_current_user, record_attempt
from app.core.security import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    cookie_kwargs,
    create_access_token,
)
from app.modules.auth import service
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        ACCESS_COOKIE,
        access,
        **cookie_kwargs(settings.access_token_minutes * 60),
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        **cookie_kwargs(settings.refresh_token_days * 24 * 3600),
    )


def _clear_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    check_rate_limit(get_client_ip(request))
    user = await service.register_user(db, body.username, body.password)
    access, refresh = await service.issue_session(db, user)
    _set_cookies(response, access, refresh)
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    check_rate_limit(get_client_ip(request))
    record_attempt(get_client_ip(request))
    user = await service.authenticate_user(db, body.username, body.password)
    access, refresh = await service.issue_session(db, user)
    _set_cookies(response, access, refresh)
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing.",
        )
    user, new_refresh = await service.rotate_refresh_token(db, raw)
    access = create_access_token(
        user.id, {"username": user.username, "role": user.role}
    )
    _set_cookies(response, access, new_refresh)
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await service.revoke_refresh_token(db, request.cookies.get(REFRESH_COOKIE, ""))
    _clear_cookies(response)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)