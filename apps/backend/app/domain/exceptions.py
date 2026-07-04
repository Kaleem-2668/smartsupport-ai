class DomainError(Exception):
    """Base class for business-rule violations. Endpoints translate these to HTTP codes."""


class EmailAlreadyExistsError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class InactiveUserError(DomainError):
    pass


class InvalidTokenError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass


class DocumentNotFoundError(DomainError):
    pass


class InvalidFileError(DomainError):
    pass


class StorageError(DomainError):
    pass


class ConversationNotFoundError(DomainError):
    pass


class LLMError(DomainError):
    pass
