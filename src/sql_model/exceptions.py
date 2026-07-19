class DataModelError(Exception):
    """Base exception for the data-model package."""

    pass


class DatabaseConnectionError(DataModelError):
    """Raised when database connection fails."""

    pass


class SessionError(DataModelError):
    """Raised when session operation fails."""

    pass


class TransactionError(DataModelError):
    """Raised when transaction operation fails."""

    pass


class NotFoundError(DataModelError):
    """Raised when a requested entity does not exist."""

    pass


class ConflictError(DataModelError):
    """Raised on constraint violations or conflicts."""

    pass


class RepositoryError(DataModelError):
    """Raised when repository operation fails."""

    pass


class BulkWriteError(DataModelError):
    """Raised when direct asyncpg bulk operations fail."""

    pass
