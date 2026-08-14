from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import RefreshToken, User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    return await db.scalar(select(User).where(User.username == username))


async def register_user(db: AsyncSession, username: str, password: str) -> User:
    existing = await get_user_by_username(db, username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken.",
        )
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    user = await get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    return user


async def issue_refresh_token(db: AsyncSession, user: User) -> str:
    raw = secrets.token_urlsafe(48)
    token = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    db.add(token)
    await db.commit()
    return raw


async def rotate_refresh_token(
    db: AsyncSession, raw_token: str
) -> tuple[User, str]:
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    token = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == digest)
    )
    if token is None or token.revoked_at is not None or token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or expired. Log in again.",
        )
    user = await db.get(User, token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    token.revoked_at = datetime.now(UTC)
    new_raw = await issue_refresh_token(db, user)
    await db.commit()
    return user, new_raw


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    if not raw_token:
        return
    digest = hashlib.sha256(raw_token.encode()).hexdigest()
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token_hash == digest)
    )
    await db.commit()


async def issue_session(db: AsyncSession, user: User) -> tuple[str, str]:
    access = create_access_token(user.id, {"username": user.username, "role": user.role})
    refresh = await issue_refresh_token(db, user)
    return access, refresh


async def seed_users(db: AsyncSession) -> None:
    for username, password in settings.seed_users.items():
        existing = await get_user_by_username(db, username)
        if existing is not None:
            continue
        db.add(
            User(
                id=str(uuid.uuid4()),
                username=username,
                password_hash=hash_password(password),
                role="admin" if username == "admin" else "user",
            )
        )
    await db.commit()