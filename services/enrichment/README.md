# Enrichment Service

The Enrichment Service is responsible for transforming raw scraped data into structured intelligence. It coordinates between LLMs (OpenAI) and external data providers (e.g., email finders) to augment company and lead profiles.

## Core Components

### `EnrichmentOrchestrator`
The central engine that manages the enrichment pipeline. Its primary method, `enrich_company(company_id)`, performs the following:
1.  **State Management:** Updates the company's `enrichment_status` to `PROCESSING`.
2.  **Parallel Execution:** Executes LLM-based summarization and external email finding concurrently using `asyncio.gather`.
3.  **Partial Success Handling:** If one sub-task fails (e.g., an external API is down), it allows the other to proceed, marking the status as `DONE` but logging warnings for the failed parts.
4.  **Persistence:** Saves enriched data back to the `Company` model and logs the operation in the `Enrichment` audit table.
5.  **Downstream Triggering:** Publishes a job to the Embedding queue upon successful completion.

### External API Providers (`external_apis/`)
To decouple the orchestrator from specific vendors, the service uses a provider pattern:
-   **`BaseEnrichmentProvider`:** An abstract base class defining the `find_emails` interface.
-   **`MockEnrichmentProvider`:** Returns deterministic mock data for local development and testing without hitting paid APIs.
-   **`HunterEnrichmentProvider`** (TODO): Future implementation for integration with Hunter.io.

## Configuration

Enrichment behavior is controlled via environment variables (see `core/config.py`):
-   `ENRICHMENT_PROVIDER`: Set to `mock` (default) or `hunter`.
-   `HUNTER_API_KEY`: Required if using the Hunter provider.

## Workflow Integration

1.  **Job Trigger:** A job is enqueued in the `enrich` Redis queue (typically by the Scrape Worker).
2.  **Worker Execution:** The `enrich_worker` pulls the job and calls `orchestrator.enrich_company()`.
3.  **LLM Enrichment:**
    -   Uses the `company_summary` prompt.
    -   Extracts industry, business model, target customer, tech stack, and growth signals.
    -   Validates output against the `CompanySummaryOutput` Pydantic model.
4.  **Email Enrichment:**
    -   Extracts the domain from the company website.
    -   Queries the configured provider for contact emails.
    -   Stores results in the `social_links` JSON field.

## Testing

Integration tests for the enrichment service run within a Dockerized environment to ensure connectivity to MySQL and Redis.

### Local Integration Test
```bash
docker compose --env-file .env.docker run --rm -e ENV_FILE=.env.docker api uv run pytest tests/integration/test_enrichment.py
```

## TODOs
- [ ] Implement `HunterEnrichmentProvider` for production email discovery.
- [ ] Implement an in-house scraping/inference service for email discovery to replace external dependencies.
- [ ] Add support for lead-specific scoring and enrichment.
