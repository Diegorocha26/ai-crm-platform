# Phase 5 Implementation: Learning & Troubleshooting Summary

This document summarizes the technical hurdles encountered during the implementation and testing of the Enrichment Orchestrator. These points serve as a reference for common issues in Dockerized Python environments.

### 1. Missing Browser Binaries (Playwright)
*   **Issue:** Scraper services failed because the Docker image had the Playwright library but not the actual Chromium browser binaries.
*   **Fix:** Added `RUN uv run playwright install --with-deps chromium` to the Dockerfiles.
*   **Learning:** System-level dependencies and browser binaries must be explicitly installed in the container, as they are not part of the Python package itself.

### 2. Docker Compose Environment Interpolation
*   **Issue:** MySQL containers were "unhealthy" because shell variables like `${MYSQL_USER}` were empty when running via `docker compose`.
*   **Fix:** Used the `--env-file .env.docker` flag during the command run to tell Compose where to look for variable interpolation on the host side.
*   **Learning:** Containers get their env vars from `env_file`, but the *Compose file itself* needs a source (defaulting to `.env`) to fill in placeholders before the containers even start.

### 3. Pydantic `extra_forbidden` Errors
*   **Issue:** Tests failed because `.env.docker` contained variables (like `mysql_root_password`) that weren't defined in the `Settings` class.
*   **Fix:** Updated `SettingsConfigDict` with `extra="allow"` in `core/config.py`.
*   **Learning:** By default, `pydantic-settings` is strict. When moving to Docker, the environment often contains "noise" variables that will break a strict settings model unless configured to ignore or allow them.

### 4. Dependency Grouping in `uv`
*   **Issue:** `uv sync --extra dev` failed during build because the project used `dependency-groups` instead of `optional-dependencies`.
*   **Fix:** Changed the build command to `uv sync --frozen --group dev`.
*   **Learning:** `uv` distinguishes between standard PEP-621 optional dependencies (extras) and its own dependency groups. Ensure Docker builds match the `pyproject.toml` structure.

### 5. `pytest-asyncio` Scope Mismatch
*   **Issue:** Tests failed with a `ScopeMismatch` error when the `engine` fixture (session-scoped) tried to interact with function-scoped async runners.
*   **Fix:** Standardized all test fixtures to `scope="function"` and removed the manual `event_loop` fixture.
*   **Learning:** Keeping fixture scopes consistent (usually all "function" for integration tests) prevents complex lifecycle conflicts in asynchronous testing.

### 6. LLM Output Validation (Literal Constraints)
*   **Issue:** The test failed because the LLM returned `null` for fields like `business_model`, which Pydantic expected to be a specific string (Literal).
*   **Fix:** Updated the Pydantic schema to allow `Optional[Literal[...]]` (i.e., `str | None`).
*   **Learning:** Real-world LLM outputs are unpredictable. Schemas must be flexible enough to handle "unknown" or "null" states while still enforcing structure on successful hits.

### 7. Stale Data in Tests (Database Sessions)
*   **Issue:** The test didn't "see" the changes made by the Orchestrator even though the DB was updated.
*   **Fix:** Added `db_session.expire_all()` to the test to force a refresh from the database.
*   **Learning:** When two different components (the Test and the Orchestrator) use different database sessions/connections, the first session may hold "stale" versions of objects in its internal cache.
