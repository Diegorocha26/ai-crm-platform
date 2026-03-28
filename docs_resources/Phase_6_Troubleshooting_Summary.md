# Phase 6 Implementation: Learning & Troubleshooting Summary

This document summarizes the technical hurdles and architectural decisions made during the implementation of the RAG (Retrieval-Augmented Generation) layer.

### 1. Qdrant API Versioning (`search` vs `query_points`)
*   **Issue:** The project used `qdrant-client` 1.17.0, which deprecated/removed the standard `.search()` and `.recommend()` methods on the `AsyncQdrantClient` in favor of a unified `.query_points()` API.
*   **Fix:** Updated the `Retriever` service to use `query_points`. For similarity ("more like this"), we passed the `company_id` directly as the `query` parameter.
*   **Learning:** High-velocity AI libraries (like Qdrant or OpenAI) often have breaking API changes between minor versions. Always verify method availability in the specific version installed.

### 2. Distributed Data Consistency (Cross-Database Sync)
*   **Issue:** Maintaining a consistent `embedded_at` timestamp between MySQL and Qdrant is difficult because they don't share a transaction.
*   **Fix:** Adopted a **"Worker as Source of Truth"** strategy. The worker generates a single `datetime.now()` object, attaches it to the model (for MySQL), and passes it to the `Indexer` (for Qdrant).
*   **Learning:** In distributed systems, avoid generating timestamps inside low-level services. Generate them once at the orchestration level (the Worker) and pass them down to ensure identical audit trails across different storage systems.

### 3. Redis Pipelining for Batch Performance
*   **Issue:** Checking cache keys for 100 companies individually created a network bottleneck (100 round-trips to Redis).
*   **Fix:** Used `async with redis.pipeline() as pipe:` to group all `GET` and `SETEX` commands into a single network packet.
*   **Learning:** Pipelining can turn a 1-second operation into a 10ms operation by eliminating network "ping" overhead for large batches.

### 4. Embedding Quality (Structured vs. Raw Text)
*   **Issue:** Initial embeddings used simple string concatenation, which caused the model to lose the semantic relationship between fields (e.g., distinguishing "Company Name" from "Target Customer").
*   **Fix:** Implemented a structured template: `f"Name: {name} \n Industry: {industry} ..."`.
*   **Learning:** Clear semantic markers in the text injected into the embedding model significantly improve the retrieval accuracy of vector searches.

### 5. `pytest-asyncio` Event Loop Closure
*   **Issue:** Integration tests failed with `RuntimeError: Event loop is closed` because global singleton clients (Redis/Qdrant) were created in the first test's loop and then reused in the second test after the first loop had closed.
*   **Fix:** Refactored services to support **Dependency Injection** and updated client getters with a `force_new=True` parameter for testing.
*   **Learning:** Singletons are convenient for production but dangerous for async testing. Services should always allow injecting client instances so tests can provide fresh connections tied to the current event loop.

### 6. Hybrid Testing Environment (Local vs. Docker)
*   **Issue:** Tests failed because the local Python environment couldn't "see" new files or database schema changes that hadn't been rebuilt into the Docker containers.
*   **Fix:** Standardized on `docker compose build api` before running tests and used `alembic upgrade head` inside the container to sync the schema.
*   **Learning:** When using a hybrid setup (Local code vs. Docker Infra), the "Code" side of the container must be rebuilt whenever source files or database migrations are added.

### 7. Alembic Sync in Docker
*   **Issue:** Alembic reported being at `head` but the database was missing columns because `pytest` had created the tables directly, skipping the migration history.
*   **Fix:** Used `alembic stamp <revision>` to force the migration history to match a specific state, then `alembic upgrade head` to apply missing changes.
*   **Learning:** Be careful when mixing direct SQLAlchemy `create_all` (common in tests) with Alembic migrations. If they get out of sync, `stamp` is the tool to reconcile them.

### 8. Event Loop Affinity in Synchronous Workers (RQ)
*   **Issue:** Workers running via `asyncio.run()` (like in RQ) create a fresh event loop for every job. Reusing global singleton clients (which bind to the *first* loop created) causes subsequent jobs to crash with "loop closed" or affinity errors.
*   **Fix:** Refactored the `embedding_worker` to instantiate fresh clients and RAG services *inside* the job function, and explicitly closed them in a `finally` block.
*   **Learning:** Task workers that bridge sync and async code must manage client lifecycles per-job. Never use module-level async singletons in a multi-loop environment without careful reset or dependency injection.
