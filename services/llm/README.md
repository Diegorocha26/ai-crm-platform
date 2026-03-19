# LLM Service

This service handles all interactions with Large Language Models (OpenAI, etc.), including prompt management, structured output parsing, and evaluation logging.

## Features

- **Prompt Registry:** Versioned YAML prompts stored in `prompts/v1/`.
- **Structured Output:** Enforced JSON schemas using Pydantic models.
- **Resilience:** Automatic retries on JSON parsing failures.
- **Observability:** Comprehensive logging of latency, token usage, and inputs/outputs to both `structlog` and MySQL (`enrichments` table).
- **Repair:** Automatic repair of malformed JSON responses using `json_repair`.

## Usage

### LLM Client

The `LLMClient` is the main entry point.

```python
from services.llm.client import LLMClient

client = LLMClient()

# Async call
result = await client.complete(
    prompt_name="company_summary",
    variables={"website_content": "..."},
    entity_id="company-123", # Optional: for DB logging
    entity_type="company"    # Optional: for DB logging
)

print(result.industry)
```

### Adding a New Prompt

1. Create a new YAML file in `services/llm/prompts/v1/<name>.yaml`.
2. Define `system` and `user` templates with variables (e.g., `{var}`).
3. Define the output schema in `schemas/llm_output.py`.
4. Update `services/llm/output_parser.py` to handle the new schema.
5. Update `PROMPT_TYPE_MAP` in `services/llm/llm_logger.py` if needed.

## Testing

Run unit tests:
```bash
uv run pytest tests/unit/test_prompt_registry.py tests/unit/test_output_parser.py
```

Run manual integration smoke test (mocks OpenAI if no key):
```bash
uv run python scripts/smoke_test_llm.py
```
