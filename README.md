# sql-model

A shared, high-performance, async-first persistence infrastructure layer using PostgreSQL, SQLAlchemy 2.0, SQLModel, asyncpg, and Alembic.

Designed for event-driven and MLOps platforms. This package contains **zero business logic** and has no knowledge of domain entities (e.g., Datasets, Models, Pipelines). Instead, it provides the standard persistence primitives to be reused across all platform microservices.

## Features

- **Async-First Database Layer**: Unified connection management with pg connection pooling, lifecycles, and graceful shutdown.
- **Automated Session Management**: Context-managed transactions with auto-commit, auto-rollback, and resource cleanup.
- **Shared Base Models**: Timezone-aware timestamp columns, UUID primary keys, and snake_case table name mapping.
- **Generic Repository Pattern**: Fast CRUD operations, simple filtering, and out-of-the-box support for:
  - Offset-based pagination
  - Cursor-based pagination (ideal for high-throughput event logs)
- **Unit of Work**: Standard database transaction coordinator guaranteeing ACID boundaries and implicit rollbacks on failure.
- **High-Performance Ingestion**: Low-level fast bulk operations using raw `asyncpg` COPY directly.
- **Alembic Helpers**: Shared naming conventions and online/offline migration runners.
- **Testing Fixtures**: Helpers for creating temporary databases and transaction-isolated unit tests.

---

## Installation

Install using `uv`:

```bash
uv add sql-model
```

---

## Usage Examples

### 1. Database & Session Management

Configure and initialize the database engine:

```python
from sql_model import Database

# Initialize database
db = Database("postgresql+asyncpg://user:pass@localhost:5432/dbname")

# Lifecycle hook
await db.connect()

# Execute operations in a session with auto-commit & auto-rollback
async with db.session() as session:
    result = await session.execute(text("SELECT 1"))

# Shutdown
await db.disconnect()
```

### 2. Base Models

Define service-specific models using the generic base table:

```python
from sql_model import BaseTable
from sqlmodel import Field

class Dataset(BaseTable, table=True):
    name: str = Field(nullable=False)
    version: str = Field(nullable=False)
```

`BaseTable` automatically generates:
- `id`: UUID primary key default-valued to `gen_random_uuid()` on DB side.
- `created_at`: Timezone-aware UTC datetime.
- `updated_at`: Timezone-aware UTC datetime with automated updates.
- `__tablename__`: Class name mapped to snake_case (`dataset`).

### 3. Repository Pattern

Interact with your models via the generic repository:

```python
from sql_model import Repository

# Bind repository to session
repo = Repository(Dataset, session)

# Retrieve by ID
dataset = await repo.get(dataset_id)

# List with filters
datasets = await repo.list(version="v1.0.0")

# Create
new_dataset = await repo.create(Dataset(name="iris", version="v1.0.0"))

# Delete
await repo.delete(dataset_id)
```

#### Pagination (Offset & Cursor)

```python
# Offset pagination
page = await repo.paginate_offset(page=1, size=10, version="v1.0.0")
print(page.items, page.total)

# Cursor pagination
cursor_page = await repo.paginate_cursor(
    cursor=None,
    size=10,
    sort_column="created_at",
    descending=True
)
print(cursor_page.items, cursor_page.next_cursor)
```

### 4. Unit of Work (UOW)

Coordinate multiple repositories within a single transaction:

```python
from sql_model import SQLUnitOfWork

# Instantiate UOW with session factory
async with SQLUnitOfWork(db.session_factory) as uow:
    # Retrieve repository bound to UOW transaction
    dataset_repo = uow.repository(Dataset)
    
    # Perform operations
    await dataset_repo.add(Dataset(name="model_run_data", version="1.0"))
    
    # Commit transaction
    await uow.commit()
    # Auto-rollback occurs on exception or if uow.commit() is not explicitly called.
```

### 5. High-Performance Bulk Writes

Direct `asyncpg` COPY ingestion bypassing the ORM for high performance:

```python
from sql_model import create_postgres_pool, BulkWriter

# Initialize direct pool
pool = await create_postgres_pool("postgresql://localhost:5432/postgres")
writer = BulkWriter(pool)

# Mass ingestion payload (uses server defaults for id, timestamps if omitted)
records = [
    {"name": f"feature_{i}", "value": i}
    for i in range(100_000)
]

# Write directly using Postgres COPY
await writer.insert_many("feature_table", records)
await pool.close()
```

---

## Testing Utilities

The package provides helpers to easily run isolated tests with transactional rollbacks.

Example `conftest.py` structure:

```python
import pytest
import pytest_asyncio
from typing import AsyncIterator
from sqlalchemy.pool import NullPool
from sql_model import Database, BaseTable, temp_database, transaction_session

@pytest.fixture(scope="session")
def admin_db_url() -> str:
    return "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

@pytest_asyncio.fixture
async def test_db_url(admin_db_url: str) -> AsyncIterator[str]:
    # Creates a temporary database and drops it after the test
    async with temp_database(admin_db_url) as url:
        yield url

@pytest_asyncio.fixture
async def test_engine(test_db_url: str):
    db = Database(test_db_url, poolclass=NullPool)
    await db.connect()
    
    async with db.engine.begin() as conn:
        await conn.run_sync(BaseTable.metadata.create_all)
        
    yield db.engine
    await db.disconnect()

@pytest_asyncio.fixture
async def session(test_engine) -> AsyncIterator:
    # Yields a transaction session that rolls back automatically
    async with transaction_session(test_engine) as sess:
        yield sess
```
