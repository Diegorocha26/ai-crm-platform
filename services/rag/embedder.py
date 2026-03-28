import hashlib
import json
import logging
from typing import List
from openai import AsyncOpenAI
from core.config import get_settings
from core.redis_client import get_redis_client

settings = get_settings()
logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, redis_client=None, openai_client=None):
        if not settings.OPENAI_API_KEY:
             raise ValueError("OpenAI API Key not configured")
        
        self.client = openai_client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.redis = redis_client or get_redis_client()
        self.model = settings.OPENAI_EMBEDDING_MODEL

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single string.
        """
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of strings, with caching.
        """
        if not texts:
            return []

        # 1. Normalize and Truncate (Cost & Error protection)
        # Limit to ~15,000 chars to stay safe within OpenAI token limits (~8k tokens)
        # TODO: for huge texts, consider if a chunking strategies separation is worth it 
        processed_texts = [t.strip()[:15000] for t in texts]

        # 2. Check Cache
        cached_embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Redis pipeline for efficiency
        async with self.redis.pipeline() as pipe:
            for i, text in enumerate(processed_texts):
                key = self._get_cache_key(text)
                pipe.get(key)
            
            results = await pipe.execute()
        
        for i, result in enumerate(results):
            # Use 'is not None' to distinguish from empty values in cache
            if result is not None:
                # TODO: Add validation/try-except for corrupted cache entries
                cached_embeddings.append((i, json.loads(result)))
            else:
                texts_to_embed.append(processed_texts[i])
                indices_to_embed.append(i)

        if not texts_to_embed:
            # All cached
            final_results = [None] * len(texts)
            for idx, embedding in cached_embeddings:
                final_results[idx] = embedding
            return final_results

        # 3. Call API for missing texts
        # TODO: Add retry logic with exponential backoff (e.g., using tenacity)
        try:
            batch_size = 100
            all_new_embeddings = []
            
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i : i + batch_size]
                response = await self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                # OpenAI preserves order in batch results
                batch_embeddings = [data.embedding for data in response.data]
                all_new_embeddings.extend(batch_embeddings)

        except Exception as e:
            logger.error(f"Embedding API failed: {e}")
            raise e

        # 4. Update Cache & Merge Results
        final_results = [None] * len(texts)
        
        # Fill cached
        for idx, embedding in cached_embeddings:
            final_results[idx] = embedding
            
        # Fill new and cache them
        async with self.redis.pipeline() as pipe:
            for i, embedding in enumerate(all_new_embeddings):
                original_idx = indices_to_embed[i]
                final_results[original_idx] = embedding
                
                key = self._get_cache_key(texts_to_embed[i])
                # Cache for 30 days
                pipe.setex(key, 60 * 60 * 24 * 30, json.dumps(embedding))
            
            await pipe.execute()

        return final_results

    def _get_cache_key(self, text: str) -> str:
        """
        Generate a unique, consistent key for a given text.
        Note: The text is already stripped and truncated in embed_batch.
        """
        hash_val = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"embedding:{self.model}:{hash_val}"
