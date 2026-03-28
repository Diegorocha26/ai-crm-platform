# RAG Service

This service handles the Retrieval-Augmented Generation (RAG) layer, including text embeddings, vector indexing in Qdrant, and semantic retrieval.

## Components

- **Embedder (`embedder.py`)**: Generates embeddings using OpenAI's `text-embedding-3-small`. Includes a Redis-based cache to minimize API costs and latency.
- **Indexer (`indexer.py`)**: Constructs searchable company profiles and upserts them into the Qdrant vector database.
- **Retriever (`retriever.py`)**: Performs semantic search, similarity recommendations ("more like this"), and metadata filtering.
- **Context Builder (`context_builder.py`)**: Orchestrates retrieval and formatting of relevant context for LLM prompt injection.

## Configuration

Settings are managed in `core/config.py` and `.env`:
- `QDRANT_HOST`: Host for the Qdrant service.
- `QDRANT_PORT`: Port for Qdrant (default 6333).
- `QDRANT_COLLECTION`: Name of the collection (default `company_profiles`).
- `OPENAI_EMBEDDING_MODEL`: OpenAI model used for embeddings (default `text-embedding-3-small`).

## Usage

### Indexing a Company
```python
from services.rag.indexer import Indexer
indexer = Indexer()
await indexer.index_company(company_object)
```

### Searching
```python
from services.rag.retriever import Retriever
retriever = Retriever()
results = await retriever.search("CRM automation startups", top_k=5)
```

### Building Context
```python
from services.rag.context_builder import ContextBuilder
builder = ContextBuilder()
context = await builder.build_context("CRM automation startups")
```
