# Spike: Data Pipeline Testing DX and Documentation Strategy

**Issue**: #435
**Date**: 2026-02-07
**Status**: Recommendation

---

## Executive Summary

Data pipeline testing is a natural fit for dioxide because every boundary in a data pipeline
is an external system (S3, Kafka, Postgres, BigQuery, Spark, APIs). The existing dioxide API
-- `@adapter.for_()`, `@service`, `Profile`, and `fresh_container` -- already handles data
pipeline dependency injection well without modification. The primary gap is not in the API
but in documentation, examples, and content that speaks directly to data engineers.

This spike recommends prioritizing documentation and content creation over framework
integrations, with one exception: a lightweight Airflow integration (M-sized effort) would
provide the highest-impact DX improvement given Airflow's dominant market position.

---

## Area 1: Documentation and Content Strategy

### 1.1 The Data Engineer's Testing Problem

Data engineers face a testing trilemma:

1. **Mock everything** -- Brittle, coupled to implementation, high maintenance. A mock of
   `boto3.client('s3').get_object()` breaks when you refactor to use `s3fs` or `smart_open`.
2. **Stand up real infrastructure** -- Slow, expensive, flaky. LocalStack, testcontainers,
   Docker Compose for Postgres+Kafka+Redis. CI takes 20 minutes.
3. **Don't test** -- The most common choice. Data pipelines are the least-tested code in
   most organizations.

dioxide's approach of defining ports (`Protocol`) for each boundary and providing fast
in-memory fakes via `Profile.TEST` is the correct answer to this problem. The challenge is
that data engineers don't typically think in terms of "ports and adapters" or "hexagonal
architecture." The documentation needs to translate these patterns into data pipeline
terminology.

### 1.2 Priority-Ranked Content to Create

#### P0: Data Pipeline Testing Guide (`docs/guides/data-pipeline-testing.md`)

**Rationale**: This is the single highest-impact piece. A dedicated guide that walks through
a realistic ETL pipeline (extract from object storage, transform with pandas/polars, load
to a database) using dioxide would directly address the pain point Sal from zofiq described.

**Proposed outline**:

1. The Problem: Why data pipelines are hard to test
2. The Solution: Ports at every boundary
3. Walk-through: Building a testable ETL pipeline
   - Define ports: `ObjectStoragePort`, `DatabasePort`, `NotificationPort`
   - Production adapters: S3, PostgreSQL, Slack
   - Test fakes: In-memory storage, in-memory tables, recorded notifications
   - Service: `IngestionPipeline` with transform logic
4. Testing: `fresh_container(profile=Profile.TEST)` with data assertions
5. Comparison: Before (mocked boto3) vs After (dioxide fakes)
6. Advanced: Lifecycle management for connection pools, multi-source joins

**Effort**: M (2-3 hours of writing)

#### P1: Data Pipeline Example (`examples/data_pipeline/`)

**Rationale**: Runnable code is worth more than documentation. An example that data engineers
can clone, run, and modify would be a powerful onboarding tool. This complements the guide.

**Proposed structure**:

```
examples/data_pipeline/
    README.md              # Setup and run instructions
    ports.py               # ObjectStoragePort, DatabasePort, MetricsPort
    adapters_prod.py       # S3Adapter, PostgresAdapter, DatadogAdapter
    adapters_test.py       # InMemoryStorageAdapter, InMemoryDatabaseAdapter
    pipeline.py            # @service IngestionPipeline with transform logic
    test_pipeline.py       # pytest tests using fresh_container
```

**Effort**: M (2-3 hours)

#### P2: Mock vs Fake Comparison Using Data Pipeline Case Study

**Rationale**: Issue #394 proposes a mock-vs-fake comparison page. A data pipeline is the
strongest possible case study because:
- The boundaries are numerous (5-10 external systems per pipeline)
- The mocks are deeply nested (`mock_s3_client.get_object.return_value.read.return_value`)
- The fakes are simple (dict-based in-memory stores)
- The maintenance burden of mocks scales with boundary count

This should be the primary case study for #394, not a web API example.

**Effort**: S (1-2 hours, combines with #394 work)

#### P3: Blog Post / dev.to Article Targeting Data Engineers

**Rationale**: Data engineers are an underserved audience for DI frameworks. A well-written
article titled something like "Stop Mocking boto3: How to Actually Test Your Data Pipelines"
would resonate strongly and drive awareness. The title targets a specific pain point that
every data engineer has experienced.

**Proposed outline**:

1. Hook: "Your data pipeline tests are lying to you" (mock fragility)
2. The problem with mocking external services (code examples)
3. Introducing the ports-and-adapters pattern (no framework yet)
4. Making it automatic with dioxide (decorator-based registration)
5. Full example: testable ETL pipeline
6. Performance comparison: mock setup vs fake setup (lines of code, test speed)
7. CTA: Link to the guide and example

**Effort**: L (half day of writing, editing, and publishing)

#### P4: Update `llms.txt` to Mention Data Pipelines

**Rationale**: LLM-powered code assistants are increasingly used by data engineers. Including
data pipeline testing as a primary use case in `llms.txt` ensures that AI assistants can
recommend dioxide for this purpose.

**Effort**: XS (15 minutes)

### 1.3 Where Does This Fit in Existing Docs?

The data pipeline testing guide fits naturally in `docs/guides/` alongside existing guides
like `choosing-decorators.md` and `lifecycle-async-patterns.md`. The guide should be
cross-linked from:

- `docs/cookbook/index.md` (recipe: "Testing Data Pipelines")
- `docs/TESTING_GUIDE.md` (reference in "Real-World Examples" section)
- `docs/why-dioxide.md` (add data pipeline use case)

---

## Area 2: DX Improvements for Data Engineers

### 2.1 Data Engineering Stack Analysis

#### Market Share (2024 PyPI Downloads)

| Orchestrator | Downloads | Market Position |
|-------------|-----------|-----------------|
| Apache Airflow | 320M | Dominant (10x nearest competitor) |
| Prefect | 32M | Strong #2 |
| Dagster | 15M | Growing #3 |
| Luigi | 5.6M | Legacy/declining |

**Source**: PyPI download statistics, 2024

#### Typical Data Engineer Stack

| Layer | Tools | Testing Pain |
|-------|-------|-------------|
| Orchestration | Airflow, Dagster, Prefect | DAG testing requires full Airflow context |
| Transformation | pandas, polars, dbt, Spark | Pure logic, easy to test in isolation |
| Object Storage | S3, GCS, Azure Blob | Requires LocalStack or real buckets |
| Databases | PostgreSQL, BigQuery, Snowflake, Redshift | Requires running instances |
| Message Queues | Kafka, RabbitMQ, SQS | Requires running brokers |
| APIs | REST, gRPC, GraphQL | Requires mock servers |
| Monitoring | Datadog, PagerDuty, Slack | Usually not tested at all |

The key insight: **transformation logic is easy to test, but boundary interactions are hard**.
dioxide addresses the hard part.

### 2.2 Framework Integration Assessment

#### Airflow Integration -- RECOMMENDED (M effort)

**Current DI story**: Airflow has no built-in dependency injection. Tasks access external
systems through Connections and Hooks, which are configured in the Airflow metadata database.
Testing requires either `airflow db init` to spin up a test database, or mocking the
`BaseHook.get_connection()` method. This is the most painful testing story of the three
major orchestrators.

**Pain points**:
- Testing custom operators requires mocking `self.get_connection()` or `Variable.get()`
- No separation between "what my task does" and "how it connects to infrastructure"
- DAG-level tests are slow because they parse the full DAG, including all imports
- Airflow 3.0 improved things with the TaskFlow API, but DI is still manual

**What a dioxide integration would look like**:

```python
from airflow.decorators import task
from dioxide import Container, Profile, adapter, service
from dioxide.airflow import configure_dioxide, Inject

# Configure dioxide once in DAG file
configure_dioxide(profile=Profile.PRODUCTION)

# Ports (defined in your domain code, not in the DAG file)
class ObjectStoragePort(Protocol):
    def read_parquet(self, path: str) -> pd.DataFrame: ...
    def write_parquet(self, path: str, df: pd.DataFrame) -> None: ...

class DatabasePort(Protocol):
    def upsert(self, table: str, df: pd.DataFrame) -> int: ...

# Services (pure business logic)
@service
class IngestionPipeline:
    def __init__(self, storage: ObjectStoragePort, db: DatabasePort):
        self.storage = storage
        self.db = db

    def run(self, source_path: str, target_table: str) -> int:
        df = self.storage.read_parquet(source_path)
        df = self._transform(df)  # Pure logic
        return self.db.upsert(target_table, df)

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # Business rules here
        return df.dropna().rename(columns={'old': 'new'})

# DAG definition
@task
def ingest(source_path: str, target_table: str):
    container = Container()
    container.scan(profile=Profile.PRODUCTION)
    pipeline = container.resolve(IngestionPipeline)
    return pipeline.run(source_path, target_table)

# Testing (no Airflow required!)
async def test_ingestion():
    async with fresh_container(profile=Profile.TEST) as container:
        pipeline = container.resolve(IngestionPipeline)
        result = pipeline.run('test/input.parquet', 'output_table')
        assert result == 5  # 5 rows upserted

        storage = container.resolve(ObjectStoragePort)
        assert 'test/input.parquet' in storage.files_read

        db = container.resolve(DatabasePort)
        assert 'output_table' in db.tables_written
```

**Integration scope**:
- `configure_dioxide(profile=...)` -- Set up container for DAG context
- Task helper or decorator that provides container access
- Documentation showing how to test tasks outside of Airflow
- No need for deep Airflow integration. The value is in extracting logic out of Airflow

**Effort**: M (the integration module is small, and the value is mostly in documentation)

**Recommendation**: The biggest value is NOT an `airflow.py` integration module. It is a
guide showing how to extract business logic out of Airflow tasks into dioxide-managed
services, making them testable without Airflow at all. An integration module would be a
thin convenience layer on top.

#### Dagster Integration -- NOT RECOMMENDED

**Current DI story**: Dagster already has excellent dependency injection via its Resources
system. Resources are typed, swappable per environment, and support nested dependencies.
The `@asset` decorator declares resource dependencies as function parameters. Dagster's
approach is philosophically very close to dioxide's ports-and-adapters pattern.

**Why not integrate**:
- Dagster's Resources system is already a good DI solution for data pipelines
- Adding dioxide on top would be redundant and confusing
- Dagster users who want dioxide-style patterns can already achieve them natively
- The effort would be spent competing with a good solution rather than filling a gap

**Instead**: Write a comparison document showing how Dagster Resources map to dioxide
concepts. This helps users who already know Dagster understand dioxide, and vice versa.

**Effort if we did it**: L (significant surface area, unclear value)

#### Prefect Integration -- LOW PRIORITY

**Current DI story**: Prefect uses Blocks for configuration and infrastructure management.
Blocks are typed, versioned, and stored in a backend. However, Blocks are more of a
configuration system than a DI system -- they don't compose dependencies the way dioxide
or Dagster Resources do.

**Pain points**:
- Testing flows requires mocking Blocks or creating test Block instances
- No automatic dependency resolution (manual wiring)
- Less painful than Airflow because Prefect flows are "just Python"

**What an integration might look like**: Similar to the Celery integration -- a
`configure_dioxide()` function and a flow decorator. However, since Prefect flows are
already "just Python," the value of a formal integration is lower. Users can use dioxide's
Container directly in their flows.

**Recommendation**: Document the pattern but don't build a formal integration module yet.
Revisit if user demand emerges.

**Effort if we did it**: S-M

#### dbt Integration -- NOT APPLICABLE

dbt is SQL-centric and operates at the transformation layer. There are no Python boundaries
to inject. Not applicable for dioxide.

### 2.3 Common Data Pipeline Boundary Interfaces

These are the ports that data engineers would define when using dioxide:

| Boundary | Port Example | Production Adapter | Test Fake |
|----------|-------------|-------------------|-----------|
| Object Storage | `ObjectStoragePort` | `S3Adapter` (boto3) | `InMemoryStorageAdapter` (dict) |
| Relational DB | `DatabasePort` | `PostgresAdapter` (asyncpg) | `InMemoryDatabaseAdapter` (dict of DataFrames) |
| Data Warehouse | `WarehousePort` | `BigQueryAdapter` | `InMemoryWarehouseAdapter` |
| Message Queue | `MessageQueuePort` | `KafkaAdapter` | `InMemoryQueueAdapter` (list) |
| REST API | `ApiClientPort` | `HttpApiAdapter` (httpx) | `CannedResponseAdapter` (dict) |
| Notification | `NotificationPort` | `SlackAdapter` | `RecordedNotificationAdapter` (list) |
| File System | `FileSystemPort` | `LocalFileAdapter` | `InMemoryFileAdapter` (dict) |
| Metrics | `MetricsPort` | `DatadogAdapter` | `InMemoryMetricsAdapter` (list) |

The existing dioxide API handles all of these well. No API changes are needed.

### 2.4 API Fitness Assessment

#### Does the existing API work for data pipelines?

**Yes.** The `@adapter.for_()` / `@service` / `Profile` pattern maps cleanly to data pipeline
architecture:

| Data Pipeline Concept | dioxide Concept |
|----------------------|----------------|
| External system boundary | Port (`Protocol`) |
| Real implementation (S3, PG) | `@adapter.for_(Port, profile=Profile.PRODUCTION)` |
| Test fake (in-memory) | `@adapter.for_(Port, profile=Profile.TEST)` |
| Pipeline logic | `@service` |
| Environment switching | `Profile.PRODUCTION` vs `Profile.TEST` |
| Connection lifecycle | `@lifecycle` (initialize/dispose) |
| Per-task isolation | `fresh_container()` or `Scope.FACTORY` |

#### Potential Rough Edges

1. **Synchronous vs asynchronous**: Many data pipeline tools (Airflow, pandas) are synchronous.
   dioxide's `@lifecycle` requires async `initialize()`/`dispose()`. This is fine for the
   container lifecycle, but users might expect sync lifecycle methods. The current API handles
   this with `asyncio.run()` in integration modules (see `celery.py`), which is acceptable.

2. **DataFrame-heavy workflows**: Data engineers work extensively with DataFrames. The
   documentation should show fake adapters that return and accept DataFrames, not just
   simple types. Example:

   ```python
   class ObjectStoragePort(Protocol):
       def read_parquet(self, path: str) -> pd.DataFrame: ...
       def write_parquet(self, path: str, df: pd.DataFrame) -> None: ...

   @adapter.for_(ObjectStoragePort, profile=Profile.TEST)
   class InMemoryStorageAdapter:
       def __init__(self) -> None:
           self.files: dict[str, pd.DataFrame] = {}

       def read_parquet(self, path: str) -> pd.DataFrame:
           return self.files[path]

       def write_parquet(self, path: str, df: pd.DataFrame) -> None:
           self.files[path] = df.copy()

       def seed(self, path: str, df: pd.DataFrame) -> None:
           self.files[path] = df.copy()
   ```

3. **Functional vs OOP style**: Data engineers tend toward a more functional style (functions
   operating on DataFrames) versus the class-based approach dioxide uses. The guide should
   acknowledge this and show how dioxide services can wrap functional logic:

   ```python
   @service
   class TransformPipeline:
       def __init__(self, storage: ObjectStoragePort, db: DatabasePort):
           self.storage = storage
           self.db = db

       def run(self, source: str, target: str) -> int:
           df = self.storage.read_parquet(source)
           df = clean_nulls(df)          # Pure function
           df = normalize_columns(df)     # Pure function
           df = apply_business_rules(df)  # Pure function
           return self.db.upsert(target, df)
   ```

   The key message: dioxide manages the boundaries (constructor injection), and transformation
   logic can remain functional. The service class is just a composition point.

4. **Multi-binding for plugin pipelines**: The existing `multi=True` parameter on
   `@adapter.for_()` already supports plugin-style pipelines where multiple transform steps
   are registered and executed in priority order. This is a natural fit for data pipeline
   step composition but should be documented with a data pipeline example.

#### API Concerns to Address Before Promoting to Data Engineers

None are blocking. The API is ready. The gaps are purely in documentation and examples.

### 2.5 Data-Specific Fake Patterns

Should dioxide provide reusable fake implementations? **No, not as part of core.**

Providing fake adapters in the dioxide package would violate the framework's design
philosophy of being domain-agnostic. However, the documentation should include thorough
examples of fake patterns for common data boundaries, which users can copy and adapt.

A potential future direction is a `dioxide-data-fakes` companion package, but this should
only be considered after establishing demand through documentation and user feedback.

---

## Example Code Sketch: Testable ETL Pipeline

This is a complete, realistic example showing how dioxide enables testing of a data pipeline
that reads from S3, transforms with pandas, and loads to PostgreSQL.

```python
# ports.py -- Define boundaries as protocols
from typing import Protocol
import pandas as pd


class ObjectStoragePort(Protocol):
    def read_parquet(self, path: str) -> pd.DataFrame: ...
    def write_parquet(self, path: str, df: pd.DataFrame) -> None: ...


class DatabasePort(Protocol):
    def upsert(self, table: str, df: pd.DataFrame) -> int: ...
    def read_table(self, table: str) -> pd.DataFrame: ...


class NotificationPort(Protocol):
    def send_success(self, message: str) -> None: ...
    def send_failure(self, message: str, error: str) -> None: ...
```

```python
# adapters_prod.py -- Real implementations for production
import boto3
import pandas as pd
import sqlalchemy
from dioxide import adapter, lifecycle, Profile


@adapter.for_(ObjectStoragePort, profile=Profile.PRODUCTION)
@lifecycle
class S3Adapter:
    def __init__(self) -> None:
        self.client = None

    async def initialize(self) -> None:
        self.client = boto3.client("s3")

    async def dispose(self) -> None:
        self.client = None

    def read_parquet(self, path: str) -> pd.DataFrame:
        bucket, key = path.split("/", 1)
        obj = self.client.get_object(Bucket=bucket, Key=key)
        return pd.read_parquet(obj["Body"])

    def write_parquet(self, path: str, df: pd.DataFrame) -> None:
        bucket, key = path.split("/", 1)
        buffer = df.to_parquet()
        self.client.put_object(Bucket=bucket, Key=key, Body=buffer)


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    def __init__(self) -> None:
        self.engine = None

    async def initialize(self) -> None:
        import os

        self.engine = sqlalchemy.create_engine(os.environ["DATABASE_URL"])

    async def dispose(self) -> None:
        if self.engine:
            self.engine.dispose()

    def upsert(self, table: str, df: pd.DataFrame) -> int:
        return df.to_sql(table, self.engine, if_exists="replace", index=False)

    def read_table(self, table: str) -> pd.DataFrame:
        return pd.read_sql_table(table, self.engine)


@adapter.for_(NotificationPort, profile=Profile.PRODUCTION)
class SlackAdapter:
    def send_success(self, message: str) -> None:
        import os, httpx

        httpx.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": f"SUCCESS: {message}"})

    def send_failure(self, message: str, error: str) -> None:
        import os, httpx

        httpx.post(
            os.environ["SLACK_WEBHOOK_URL"],
            json={"text": f"FAILURE: {message}\nError: {error}"},
        )
```

```python
# adapters_test.py -- Fast in-memory fakes for testing
import pandas as pd
from dioxide import adapter, Profile


@adapter.for_(ObjectStoragePort, profile=Profile.TEST)
class InMemoryStorageAdapter:
    def __init__(self) -> None:
        self.files: dict[str, pd.DataFrame] = {}
        self.files_read: list[str] = []
        self.files_written: list[str] = []

    def read_parquet(self, path: str) -> pd.DataFrame:
        self.files_read.append(path)
        if path not in self.files:
            raise FileNotFoundError(f"No file at {path}")
        return self.files[path].copy()

    def write_parquet(self, path: str, df: pd.DataFrame) -> None:
        self.files_written.append(path)
        self.files[path] = df.copy()

    def seed(self, path: str, df: pd.DataFrame) -> None:
        self.files[path] = df.copy()


@adapter.for_(DatabasePort, profile=Profile.TEST)
class InMemoryDatabaseAdapter:
    def __init__(self) -> None:
        self.tables: dict[str, pd.DataFrame] = {}
        self.tables_written: list[str] = []

    def upsert(self, table: str, df: pd.DataFrame) -> int:
        self.tables_written.append(table)
        self.tables[table] = df.copy()
        return len(df)

    def read_table(self, table: str) -> pd.DataFrame:
        if table not in self.tables:
            return pd.DataFrame()
        return self.tables[table].copy()


@adapter.for_(NotificationPort, profile=Profile.TEST)
class RecordedNotificationAdapter:
    def __init__(self) -> None:
        self.successes: list[str] = []
        self.failures: list[tuple[str, str]] = []

    def send_success(self, message: str) -> None:
        self.successes.append(message)

    def send_failure(self, message: str, error: str) -> None:
        self.failures.append((message, error))
```

```python
# pipeline.py -- Core business logic (no knowledge of S3, Postgres, or Slack)
import pandas as pd
from dioxide import service


@service
class IngestionPipeline:
    def __init__(
        self,
        storage: ObjectStoragePort,
        db: DatabasePort,
        notifications: NotificationPort,
    ):
        self.storage = storage
        self.db = db
        self.notifications = notifications

    def run(self, source_path: str, target_table: str) -> int:
        try:
            df = self.storage.read_parquet(source_path)
            df = self._transform(df)
            rows = self.db.upsert(target_table, df)
            self.notifications.send_success(
                f"Ingested {rows} rows from {source_path} to {target_table}"
            )
            return rows
        except Exception as e:
            self.notifications.send_failure(
                f"Failed to ingest {source_path}", str(e)
            )
            raise

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(subset=["user_id", "event_type"])
        df["event_date"] = pd.to_datetime(df["event_date"])
        df["user_id"] = df["user_id"].astype(str)
        return df
```

```python
# test_pipeline.py -- Fast, reliable tests with no infrastructure
import pandas as pd
import pytest
from dioxide import Profile
from dioxide.testing import fresh_container


class DescribeIngestionPipeline:
    @pytest.fixture
    async def container(self):
        async with fresh_container(profile=Profile.TEST) as c:
            yield c

    @pytest.fixture
    def pipeline(self, container):
        return container.resolve(IngestionPipeline)

    @pytest.fixture
    def storage(self, container):
        return container.resolve(ObjectStoragePort)

    @pytest.fixture
    def db(self, container):
        return container.resolve(DatabasePort)

    @pytest.fixture
    def notifications(self, container):
        return container.resolve(NotificationPort)

    def it_ingests_valid_data(self, pipeline, storage, db, notifications):
        source_data = pd.DataFrame({
            "user_id": ["u1", "u2", "u3"],
            "event_type": ["click", "purchase", "click"],
            "event_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        })
        storage.seed("raw/events.parquet", source_data)

        rows = pipeline.run("raw/events.parquet", "clean_events")

        assert rows == 3
        assert "clean_events" in db.tables
        assert len(db.tables["clean_events"]) == 3
        assert len(notifications.successes) == 1

    def it_drops_rows_with_missing_user_id(self, pipeline, storage, db):
        source_data = pd.DataFrame({
            "user_id": ["u1", None, "u3"],
            "event_type": ["click", "purchase", "click"],
            "event_date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        })
        storage.seed("raw/events.parquet", source_data)

        rows = pipeline.run("raw/events.parquet", "clean_events")

        assert rows == 2  # One row dropped

    def it_notifies_on_failure(self, pipeline, storage, notifications):
        # No file seeded -- read will fail

        with pytest.raises(FileNotFoundError):
            pipeline.run("missing/file.parquet", "output")

        assert len(notifications.failures) == 1
        assert "missing/file.parquet" in notifications.failures[0][0]

    def it_converts_event_date_to_datetime(self, pipeline, storage, db):
        source_data = pd.DataFrame({
            "user_id": ["u1"],
            "event_type": ["click"],
            "event_date": ["2026-01-15"],
        })
        storage.seed("raw/events.parquet", source_data)

        pipeline.run("raw/events.parquet", "clean_events")

        result = db.tables["clean_events"]
        assert pd.api.types.is_datetime64_any_dtype(result["event_date"])
```

### What Makes This Example Compelling

1. **Zero infrastructure**: Tests run in milliseconds with no Docker, LocalStack, or database
2. **Real assertions**: Tests verify actual data transformations, not mock call counts
3. **Refactor-safe**: Switching from boto3 to s3fs changes only the S3Adapter, not any tests
4. **Readable**: The pipeline service reads like a specification, not like test infrastructure
5. **Complete error coverage**: Failure paths are tested through the fake notification adapter

---

## Concrete Next Steps (Issueifiable)

### Content / Documentation

| Priority | Issue Title | Effort | Dependencies |
|----------|------------|--------|-------------|
| P0 | docs: Add data pipeline testing guide | M | None |
| P1 | docs: Add data pipeline example in examples/ | M | P0 (for consistency) |
| P2 | docs: Use data pipeline case study for mock-vs-fake comparison | S | #394 |
| P3 | docs: Write dev.to article targeting data engineers | L | P0 (for code examples) |
| P4 | docs: Add data pipeline mention to llms.txt | XS | None |
| P5 | docs: Add data pipeline use case to why-dioxide.md | XS | P0 |

### DX Improvements

| Priority | Issue Title | Effort | Dependencies |
|----------|------------|--------|-------------|
| P0 | docs: Add Airflow integration guide (no integration module) | M | P0 content |
| P1 | feat: Add lightweight Airflow integration module | M | P0 guide |
| P2 | docs: Add Dagster concepts comparison page | S | None |
| P3 | docs: Document common data pipeline fake patterns | S | P0 content |

### NOT Recommended (Defer or Skip)

| Item | Reason |
|------|--------|
| Dagster integration module | Dagster's Resources system already provides good DI |
| Prefect integration module | Prefect flows are "just Python," no formal integration needed |
| dbt integration | Not applicable (SQL-centric) |
| `dioxide-data-fakes` package | Premature. Document patterns first, gauge demand |
| Sync lifecycle methods | Would complicate the API. `asyncio.run()` wrapper is sufficient |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Data engineers find class-based DI too OOP | Medium | Guide emphasizes services as thin composition wrappers around functional logic |
| Airflow users expect deeper integration (operators, hooks) | Low | Guide focuses on extracting logic OUT of Airflow, which is the real value |
| Competing with Dagster's native DI story | Low | Position as complementary, not competing. dioxide works across orchestrators |
| Content effort exceeds estimates | Medium | Start with P0 guide. Each piece is independently valuable |

---

## Decision Record

**Decision**: Prioritize documentation and content (P0-P2) over framework integrations.
The dioxide API is already well-suited for data pipeline testing. The gap is in awareness
and education, not in technical capability.

**Rationale**: The example code sketch above required zero API changes. Every concept --
ports, adapters, services, profiles, lifecycle, fakes, fresh_container -- already exists
and works correctly for data pipeline use cases.

**Next action**: File individual issues for P0-P2 content items and begin work on the
data pipeline testing guide.
