"""
API dependencies - database session, authentication
"""
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.core.config import settings
from app.db.session import get_db

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get current user from JWT token (via Authorization header)"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise UnauthorizedException()

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException()

    return {"id": int(user_id), "openid": payload.get("openid")}


async def get_current_user_optional_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))] = None,
    token: str | None = Query(default=None, description="JWT token as query parameter"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> dict:
    """Get current user from JWT token, supporting both header and query parameter"""
    token_value = None
    if credentials:
        token_value = credentials.credentials
    elif token:
        token_value = token

    if not token_value:
        raise UnauthorizedException()

    payload = decode_access_token(token_value)
    if payload is None:
        raise UnauthorizedException()

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException()

    return {"id": int(user_id), "openid": payload.get("openid")}


# Type aliases for dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentUserOptional = Annotated[dict, Depends(get_current_user_optional_token)]