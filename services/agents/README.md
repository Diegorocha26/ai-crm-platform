# Agent Layer Service

The Agent Layer is the orchestration engine that chains LLM intelligence, RAG retrieval, and database operations to perform high-level CRM tasks. It provides lightweight, task-oriented agents that follow a "Think → Act → Observe" pattern for outreach, scoring, and discovery.

## Core Components

### `BaseAgent` (`base_agent.py`)
The abstract foundation for all agents. It provides a standardized interface and injects essential shared services:
- **`LLMClient`**: For intelligent reasoning and content generation.
- **`Retriever`**: For semantic context and similarity search.
- **`AsyncSessionLocal`**: For persistent state management in MySQL.

### `OutreachAgent` (`outreach_agent.py`)
Automates the creation of hyper-personalized cold emails for leads.
1.  **Context Assembly:** Fetches lead details and their associated company profile.
2.  **RAG Enrichment:** Queries the vector store for recent news, industry trends, or similar company insights to find personalization "hooks."
3.  **Generation:** Executes the `outreach_generation` prompt via the LLM Service.
4.  **Persistence:** Saves the resulting email to the `generated_content` table (type: `OUTREACH_EMAIL`) for review.

### `ScoringAgent` (`scoring_agent.py`)
Evaluates lead quality and fit for B2B sales development.
1.  **Profile Loading:** Retrieves full lead and company context.
2.  **LLM Assessment:** Uses the `lead_scoring` prompt to generate a base score and detailed reasoning.
3.  **Rule-Based Adjustments:** Applies deterministic business logic (e.g., boosting VP/CXO seniority levels or penalizing non-decision makers).
4.  **DB Update:** Synchronizes the final calculated `relevance_score` back to the `leads` table.

### `SimilarityAgent` (`similarity_agent.py`)
Facilitates "lookalike" discovery for account-based marketing (ABM).
1.  **Vector Search:** Performs a "more like this" query in Qdrant using the target company's embedding.
2.  **Data Hydration:** Automatically resolves the resulting vector IDs into full `Company` ORM objects from MySQL.

## Usage

Agents are designed to be used independently or as part of a larger workflow (e.g., an API endpoint or a background worker).

```python
from services.agents import OutreachAgent, ScoringAgent

# 1. Score a lead
scoring_agent = ScoringAgent()
score_result = await scoring_agent.run({"lead_id": "uuid-123"})
print(f"Lead Score: {score_result.score} - {score_result.reasoning}")

# 2. Generate outreach
outreach_agent = OutreachAgent()
email = await outreach_agent.run({
    "lead_id": "uuid-123",
    "value_proposition": "Our AI CRM reduces manual entry by 80%."
})
print(f"Subject: {email.subject}")
```

## Testing

### Unit Tests
Verified with mocked LLM and RAG services to ensure internal logic and rule-based adjustments are correct.
```bash
docker compose --env-file .env.docker run --rm --no-deps -e ENV_FILE=.env.docker api uv run pytest tests/unit/test_agents.py
```

### Manual Verification
A dedicated script is available to run agents against real seeded data in the database.
```bash
uv run python scripts/test_agents.py
```

## Prompt Schemas
Agents rely on structured output defined in `schemas/llm_output.py`:
- `LeadScoreOutput`: Contains `score`, `reasoning`, `key_factors`, and `recommended_action`.
- `OutreachOutput`: Contains `subject`, `body`, `tone`, and `personalization_hooks`.

# TODO: check