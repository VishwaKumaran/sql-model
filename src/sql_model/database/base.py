import uuid
from datetime import datetime, timezone
import re
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime, Column, text, MetaData
from sqlalchemy.orm import declared_attr

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
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
        ),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("TIMEZONE('utc', CURRENT_TIMESTAMP)"),
            onupdate=lambda: datetime.now(timezone.utc),
        ),
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Automatically generate table name from class name in snake_case."""
        name = cls.__name__
        pattern = re.compile(r"(?<!^)(?=[A-Z])")
        return pattern.sub("_", name).lower()
