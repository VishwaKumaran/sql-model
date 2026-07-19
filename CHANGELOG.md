# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-19

### Added
- Core `Database` connection management class using SQLAlchemy `AsyncEngine` and connection pooling.
- `BaseTable` model inheriting from SQLModel featuring automated UUID primary keys, timezone-aware UTC timestamps (`created_at`, `updated_at`), and automatic snake_case table name mapping.
- Standardized database naming conventions applied to global SQLModel metadata.
- Centralized `manage_session` context manager with automatic rollback/commit boundaries.
- Generic `Repository` class implementing CRUD operations (`get`, `list`, `create`/`add`, `update`, `delete`).
- Offset-based and cursor-based pagination utilities.
- `SQLUnitOfWork` manager implementing the transaction coordination pattern.
- High-performance Direct Postgres `BulkWriter` using `asyncpg` COPY capabilities.
- Programmatic Alembic migration helper functions (`run_migrations_online` and `run_migrations_offline`).
- Automated testing fixtures (`temp_database` and `transaction_session`).
- Fully comprehensive unit & integration tests covering database lifecycle, repositories, pagination, unit of work, and direct bulk operations.
