from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.domain.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.domain.schemas.auth import LoginRequest, RefreshRequest
from app.domain.schemas.token import Token
from app.domain.schemas.user import UserCreate, UserRead
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> User:
    try:
        return await auth_service.register(data)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    try:
        user = await auth_service.authenticate(data.email, data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except InactiveUserError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return auth_service.issue_tokens(user)


@router.post("/refresh", response_model=Token)
async def refresh(
    data: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    try:
        return await auth_service.refresh_access_token(data.refresh_token)
    except (InvalidTokenError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
