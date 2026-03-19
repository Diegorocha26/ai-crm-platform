import time
import asyncio
from typing import Any
import openai
from openai import AsyncOpenAI
from core.config import get_settings
from services.llm.prompt_registry import registry
from services.llm.output_parser import OutputParser, LLMOutputParseError
from services.llm.llm_logger import log_call

settings = get_settings()

# TODO: use litellm for seemless integration of local or cloud models
class LLMClient:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
        
        self.parser = OutputParser()
        
        # Mapping prompt names to parser methods for scalability
        self._parsers = {
            "company_summary": self.parser.parse_company_summary,
            "lead_scoring": self.parser.parse_lead_score,
            "outreach_generation": self.parser.parse_outreach,
        }

    async def complete(
        self,
        prompt_name: str,
        variables: dict[str, Any],
        version: str = "v1",
        use_local: bool = False,
        entity_id: str | None = None,
        entity_type: str | None = None
    ) -> Any:
        """
        Execute LLM completion with prompt management, parsing, and logging.
        Includes exponential backoff and retries for transient API and parsing errors.
        """
        # 1. Early Validation
        if use_local:
             # TODO: Implement Ollama/Local routing (Phase 4/5)
             raise NotImplementedError("Local LLM support not yet implemented")

        if not self.client:
             raise ValueError("OpenAI API Key not configured")

        parser_func = self._parsers.get(prompt_name)
        if not parser_func:
            raise ValueError(f"No parser defined for prompt: {prompt_name}")

        # 2. Load and Render Prompt
        template = registry.load_prompt(prompt_name, version)
        messages_dict = registry.render_prompt(template, variables)
        
        system_msg = messages_dict["system"]
        user_msg = messages_dict["user"]

        start_time = time.time()
        retries = 3
        last_error = None
        
        # 3. Execution Loop with Retries
        for attempt in range(retries):
            try:
                # Exponential backoff: 0s, 2s, 4s...
                if attempt > 0:
                    await asyncio.sleep(2 ** attempt)

                response = await self.client.chat.completions.create(
                    model=template.model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
                    temperature=template.temperature,
                    max_tokens=template.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # Safe access to response content
                if not response.choices:
                    raise ValueError("LLM returned empty choices")
                
                raw_output = response.choices[0].message.content
                if not raw_output:
                    raise ValueError("LLM returned empty message content")

                usage = response.usage
                tokens_used = usage.total_tokens if usage else 0
                
                # 4. Parse Output
                parsed_obj = parser_func(raw_output)

                latency_ms = int((time.time() - start_time) * 1000)
                
                # 5. Log Success
                await log_call(
                    prompt_name=prompt_name,
                    model=template.model,
                    latency_ms=latency_ms,
                    raw_output=raw_output,
                    parsed_output=parsed_obj.model_dump(),
                    prompt_version=version,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    tokens_used=tokens_used
                )
                
                return parsed_obj

            except (LLMOutputParseError, openai.APIError, openai.RateLimitError, openai.APITimeoutError) as e:
                last_error = e
                # Transient errors trigger a retry
                continue
            except Exception as e:
                # Critical/Unexpected errors fail immediately
                latency_ms = int((time.time() - start_time) * 1000)
                await log_call(
                    prompt_name=prompt_name,
                    model=template.model,
                    latency_ms=latency_ms,
                    raw_output=str(e),
                    parsed_output=None,
                    prompt_version=version,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    error=str(e)
                )
                raise

        # 6. If retries exhausted
        latency_ms = int((time.time() - start_time) * 1000)
        error_msg = str(last_error) if last_error else "Max retries exceeded"
        
        await log_call(
            prompt_name=prompt_name,
            model=template.model,
            latency_ms=latency_ms,
            raw_output=getattr(last_error, "raw_output", str(last_error)),
            parsed_output=None,
            prompt_version=version,
            entity_id=entity_id,
            entity_type=entity_type,
            error=error_msg
        )
        raise last_error or Exception("Max retries exceeded")
