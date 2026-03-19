import json
import structlog
from json_repair import repair_json
from pydantic import ValidationError
from schemas.llm_output import CompanySummaryOutput, LeadScoreOutput, OutreachOutput

logger = structlog.get_logger()

class LLMOutputParseError(Exception):
    """Raised when LLM output cannot be parsed into the expected schema."""
    def __init__(self, message: str, raw_output: str, repaired_output: str | None = None, errors: list | None = None):
        super().__init__(message)
        self.raw_output = raw_output
        self.repaired_output = repaired_output
        self.errors = errors

class OutputParser:
    @staticmethod
    def _parse_and_validate(raw_output: str, model_class):
        repaired_json_str = None
        try:
            # TODO: Performance - try standard json.loads(raw_output) first, 
            # only call repair_json if it fails.
            
            # 1. Try to repair JSON
            repaired_json_str = repair_json(raw_output)
            
            # 2. Load into dict
            data = json.loads(repaired_json_str)
            
            # 3. Validate with Pydantic
            # Pydantic v2 uses model_validate for dicts, or model_class(**data)
            return model_class.model_validate(data)
            
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            error_details = e.errors() if isinstance(e, ValidationError) else str(e)
            
            # Log the failure with context for debugging
            logger.error(
                "llm_parse_failure",
                model=model_class.__name__,
                error=str(e),
                raw_output=raw_output[:500] + "..." if len(raw_output) > 500 else raw_output,
                repaired_output=repaired_json_str
            )
            
            raise LLMOutputParseError(
                message=f"Failed to parse {model_class.__name__}: {str(e)}",
                raw_output=raw_output,
                repaired_output=repaired_json_str,
                errors=error_details if isinstance(error_details, list) else None
            )

    def parse_company_summary(self, raw: str) -> CompanySummaryOutput:
        return self._parse_and_validate(raw, CompanySummaryOutput)

    def parse_lead_score(self, raw: str) -> LeadScoreOutput:
        return self._parse_and_validate(raw, LeadScoreOutput)

    def parse_outreach(self, raw: str) -> OutreachOutput:
        return self._parse_and_validate(raw, OutreachOutput)
