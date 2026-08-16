import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import MetaData, text
from sqlalchemy.orm import declared_attr
from sqlmodel import DateTime, Field, SQLModel

# Standard database naming conventions to avoid platform-specific constraint name issues.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Apply naming conventions to SQLModel metadata globally
SQLModel.metadata = MetaData(naming_convention=NAMING_CONVENTION)


class BaseTable(SQLModel):
    """Base SQLModel table with UUID primary key and timezone-aware timestamps."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        sa_type=DateTime(timezone=True),
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Automatically generate table name from class name in snake_case."""
        name = cls.__name__
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
