# Specification: composable high-performance repository queries

## Problem Statement

The current repository API makes simple CRUD and equality-filtered lists easy, but becomes restrictive as soon as users need complex queries. Users must either add ad hoc repository methods or drop down to SQLAlchemy, which creates repetitive code and weakens the shared persistence conventions.

The library also needs a clear performance model. Complex reads must avoid implicit N+1 loading, unnecessary `COUNT(*)` queries, unbounded materialization, and hidden round-trips. The API must make the common path concise without pretending that a repository abstraction can replace SQLAlchemy or PostgreSQL.

## Solution

Introduce a lazy, inspectable, composable query builder behind the repository API. `Repository[Model]` remains the ergonomic entry point for entity-oriented access, while a public `Query` supports multi-model joins and projections.

The builder accepts typed SQLAlchemy expressions directly, supports explicit joins and relationship-loading options, and shares the repository's session and transaction/UoW. It exposes a small set of explicit terminal operations for cardinality, materialization, streaming, pagination, counting, and existence checks.

Existing CRUD, list, and pagination methods remain available as compatibility façades backed by the new query execution path. Complex or PostgreSQL-specific queries retain a documented SQLAlchemy escape hatch.

## User Stories

1. As a library user, I want to retrieve filtered entities with a short repository query, so that common reads require minimal code.
2. As a library user, I want to compose several filters with `AND` and `OR`, so that business search criteria do not require a new repository method for every combination.
3. As a library user, I want to use SQLAlchemy expressions directly, so that operators such as comparisons, `IN`, null checks, pattern matching, and subqueries remain available.
4. As a library user, I want invalid structural query inputs to fail explicitly before execution, so that silently ignored filters or invalid ordering cannot hide defects.
5. As a library user, I want to add deterministic ordering and limits while building a query, so that pagination and bounded reads have predictable behavior.
6. As a library user, I want to retrieve exactly one result with `one()`, so that cardinality violations are detected rather than silently accepted.
7. As a library user, I want `one_or_none()` to accept zero or one result, so that optional lookups have a clear contract.
8. As a library user, I want `first()` to return the first result or no result, so that presence checks do not require exception handling.
9. As a library user, I want `all()` to materialize a bounded result set, so that I can use ordinary collection-oriented application code.
10. As a library user, I want `exists()` to check presence efficiently, so that existence checks do not load full entities.
11. As a library user, I want `count()` to be explicit, so that an expensive count query is never added implicitly to a large read.
12. As a library user, I want to join a related model when its relationship is known, so that relational queries remain concise.
13. As a library user, I want to provide an explicit join condition when no ORM relationship exists, so that reporting and specialized queries remain possible.
14. As a library user, I want joins to filter or project data without implicitly loading relationship collections, so that joins cannot create hidden N+1 behavior.
15. As a library user, I want explicit SQLAlchemy-compatible loading options, so that I control when related entity data is materialized.
16. As a library user, I want a raiseload option available in tests, so that accidental lazy loads are detected early.
17. As a library user, I want to select only the columns needed by a use case, so that projections reduce transfer, materialization, and memory costs.
18. As a library user, I want projections to return transparent rows or scalar values, so that SQL cardinality and aliases remain visible.
19. As a library user, I want to map a projection to an explicitly supplied DTO, so that output shapes are reusable without magical DTO generation.
20. As a library user, I want projections to be read-only and untracked, so that large reads do not pay entity-tracking costs or imply update semantics.
21. As a library user, I want entity reads to retain SQLAlchemy tracking, so that normal unit-of-work updates continue to work.
22. As a library user, I want cursor pagination to be the performant default for large or changing datasets, so that later pages do not become increasingly expensive.
23. As a library user, I want a cursor to encode an opaque, versioned position, so that clients do not depend on internal column representation.
24. As a library user, I want cursor ordering to include a unique tie-breaker such as `id`, so that equal sort values do not skip or duplicate records.
25. As a library user, I want pagination to expose `has_next` and cursors without an automatic total count, so that one page can normally use one primary SQL round-trip.
26. As a library user, I want total counts to be opt-in, so that APIs can choose the expensive behavior knowingly.
27. As a library user, I want independently replayable pages, so that API handlers and jobs do not need to keep one long-lived database cursor open.
28. As a library user, I want `stream()` for sequential large-volume processing, so that memory stays bounded by the consumer rather than the full result set.
29. As a library user, I want streaming to document session, connection, and transaction lifetime, so that resource ownership is explicit.
30. As a library user, I want streaming and pagination to have separate semantics, so that I can choose between a live low-memory flow and independent windows.
31. As a library user, I want `Repository[Model]` to remain the natural entity-oriented API, so that domain code does not lose a clear ownership boundary.
32. As a library user, I want a public multi-model `Query`, so that reports and aggregate projections do not have to be owned artificially by one entity repository.
33. As a library user, I want repository queries and public queries to share the current session and transaction/UoW, so that composed work remains within one consistency boundary.
34. As a library user, I want query builders to be lazy, so that constructing a query never performs I/O.
35. As a library user, I want query builders to be inspectable and convertible to SQLAlchemy statements, so that I can understand and optimize generated SQL.
36. As a library user, I want a documented SQLAlchemy escape hatch, so that PostgreSQL-specific or highly specialized queries are not blocked by the repository abstraction.
37. As a library user, I want explicit `.unique()` behavior for entity results after collection joins, so that deduplication cost and cardinality are not hidden.
38. As a library user, I want projections never to be deduplicated implicitly, so that returned row cardinality matches the SQL query.
39. As an existing library user, I want current CRUD and simple list methods to continue working, so that adopting the new builder does not require an immediate migration.
40. As an existing library user, I want current pagination methods to use the shared query execution behavior, so that old and new APIs have consistent performance and validation.
41. As a library maintainer, I want ambiguous or silently ignored legacy inputs to be deprecated and then rejected, so that the API becomes safer without a sudden migration break.
42. As a library maintainer, I want the `update` contract to be made consistent, so that implementation and tests agree on whether the identifier is supplied separately or carried by the entity.
43. As a library maintainer, I want interactive-read benchmarks to measure latency and round-trips, so that performance claims are reproducible.
44. As a library maintainer, I want bulk/analytic benchmarks to measure throughput and memory, so that large-volume behavior is not judged by interactive latency alone.
45. As a library maintainer, I want a benchmark and diagnostic path using SQL inspection and `EXPLAIN`, so that regressions can be investigated without making diagnostics part of normal application execution.
46. As a library maintainer, I want PostgreSQL-specific capabilities such as JSONB, specialized indexes, and asyncpg/COPY to remain available, so that performance guarantees are not diluted by premature multi-database abstraction.

## Implementation Decisions

- Build the query system around a lazy query builder that composes SQLAlchemy expressions and does not perform I/O until a terminal operation is called.
- Keep the builder inspectable and convertible to a SQLAlchemy statement.
- Make `repo.query()` the ergonomic entry point for entity queries and expose a public `Query` for multi-model projections.
- Share the repository/UoW session and transaction; query objects must not create their own sessions.
- Accept native typed SQLAlchemy filter expressions and add only small helpers for common ergonomics.
- Support relationship-based joins and explicit joins with an `onclause`.
- Separate `join()` semantics from relationship loading. Provide explicit SQLAlchemy-compatible `options(...)`, including test-time `raiseload`.
- Provide `one`, `one_or_none`, `first`, `all`, `stream`, `paginate`, `count`, and `exists` as the standard read terminals.
- Keep bulk mutations separate and explicit from read-query terminals.
- Preserve entity tracking for entity-oriented reads and use untracked scalar/row results for projections and large read-only operations.
- Provide explicit DTO mapping rather than automatic DTO generation.
- Make cursor pagination the performance-oriented default for large or changing datasets. Use deterministic ordering with a unique tie-breaker, opaque/versioned cursor data, and optional totals.
- Keep offset pagination available where page numbers or small datasets make it appropriate.
- Make `.unique()` explicit for entity results affected by collection joins; never deduplicate projections implicitly.
- Preserve existing CRUD, list, and pagination methods as compatibility façades, backed by the new query execution path.
- Correct and standardize the existing `update` contract during migration, with tests defining the public behavior.
- Provide a versioned and documented SQLAlchemy escape hatch for specialized PostgreSQL queries.
- Keep PostgreSQL, SQLAlchemy 2.x, SQLModel, async-first execution, asyncpg, and COPY within the first-version support boundary.
- Add reproducible benchmarks for interactive reads and bulk/analytic processing, with initial relative targets: one primary round-trip per page, zero per-row relationship queries, no implicit relationship loading, and projection memory bounded by page/consumer size.

## Testing Decisions

- Test the public `Repository`/`Query` seam with integration tests using the existing async session and test database setup.
- Test external behavior and contracts: generated result shapes, cardinality behavior, query laziness, validation errors, session/transaction reuse, tracking mode, pagination progress, stream resource behavior, and compatibility façades.
- Cover composable filters, joins with and without relationships, explicit loading options, `raiseload`, projections, DTO mapping, entity uniqueness, cursor ordering/tie-breaking, optional counts, and offset compatibility.
- Verify that common paginated reads use one primary SQL round-trip and that relationship access does not cause N+1 queries when explicit loading is not requested.
- Verify that projection and streaming paths do not materialize the entire result set.
- Verify `one`, `one_or_none`, and `first` against empty, singleton, and multi-row results.
- Add regression tests for the standardized `update` signature and existing CRUD/list behavior.
- Add benchmark scenarios for interactive filtered pagination, multi-table projection, aggregation, and large sequential processing. Benchmarks should report latency, round-trips, throughput, and memory rather than assert fragile hardware-specific absolute thresholds initially.
- Use the repository's existing test style and database-backed async fixtures as prior art; prefer integration coverage at the highest public seam over tests of builder internals.

## Out of Scope

- A database-agnostic query DSL or guarantees for non-PostgreSQL databases.
- Automatic DTO generation or automatic projection shape inference.
- Implicit relationship loading, implicit `COUNT(*)`, or hidden N+1 mitigation that changes query shape without user intent.
- Replacing SQLAlchemy with a new ORM or hiding all SQLAlchemy capabilities behind a custom abstraction.
- A general-purpose authorization, caching, search-index, or data-loader layer.
- Bulk mutation APIs as part of the read query terminals; existing asyncpg/COPY bulk infrastructure remains a separate concern.
- Snapshot-consistent pagination across an arbitrarily long-lived client interaction.
- Immediate removal of the existing repository API.

## Further Notes

- The domain glossary for this feature is recorded in `CONTEXT.md`, including the definitions of repository, composable query, projection, pagination, tracking, stream, cursor, interactive read, and bulk/analytic processing.
- The design deliberately offers progressive disclosure: one-line simple reads, composable query construction for advanced reads, and SQLAlchemy escape hatches for specialized work.
- Existing unrelated working-tree changes must be preserved while implementing this specification.
- Publish this specification as a GitHub issue in `VishwaKumaran/sql-model` with the `ready-for-agent` label.
