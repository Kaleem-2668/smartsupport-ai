from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.exceptions import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.domain.schemas.token import Token
from app.domain.schemas.user import UserCreate
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Business rules for registration, login, and token refresh.
    Knows nothing about HTTP — fully unit-testable in isolation.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def register(self, data: UserCreate) -> User:
        existing = await self._users.get_by_email(data.email)
        if existing is not None:
            raise EmailAlreadyExistsError(f"An account with {data.email} already exists")

        return await self._users.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password")
        if not user.is_active:
            raise InactiveUserError("This account has been deactivated")
        return user

    def issue_tokens(self, user: User) -> Token:
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        user_id = decode_token(refresh_token, expected_type="refresh")
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UserNotFoundError("User no longer exists or is inactive")

        # Refresh token is reissued alongside the access token (rotation) so a
        # compromised refresh token has a shrinking window of validity.
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )
