import yaml
from typing import Any
from pathlib import Path
from pydantic import BaseModel, ValidationError
from jinja2 import Environment, StrictUndefined

class PromptTemplate(BaseModel):
    name: str
    version: str
    model: str
    temperature: float
    max_tokens: int
    system: str
    user: str

class PromptRegistry:
    def __init__(self, prompts_dir: str | Path = None):
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            self.prompts_dir = Path(__file__).parent / "prompts"
        
        self._cache: dict[str, PromptTemplate] = {}
        # Using StrictUndefined ensures we fail if a required variable is missing in Jinja
        self._jinja_env = Environment(undefined=StrictUndefined)

    def load_prompt(self, name: str, version: str = "v1", force_reload: bool = False) -> PromptTemplate:
        """
        Load a prompt template from disk or cache.
        Validates structure and version consistency.
        """
        cache_key = f"{name}:{version}"
        if not force_reload and cache_key in self._cache:
            return self._cache[cache_key]

        file_path = self.prompts_dir / version / f"{name}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in prompt {name}: {e}")

        # 1. Validate YAML is a dictionary
        if not isinstance(data, dict):
            raise ValueError(f"Prompt file {file_path} must be a valid YAML dictionary")

        # 2. Validate version consistency
        if "version" in data and str(data["version"]) != version:
            raise ValueError(
                f"Version mismatch in {file_path}: "
                f"File content has '{data['version']}' but path is '{version}'"
            )

        # 3. Pydantic validation of fields
        try:
            template = PromptTemplate(**data)
        except ValidationError as e:
            raise ValueError(f"Prompt {name} has invalid structure: {e}")

        self._cache[cache_key] = template
        return template

    def render_prompt(self, template: PromptTemplate, variables: dict[str, Any]) -> dict[str, str]:
        """
        Render system and user messages using Jinja2.
        Safely handles braces {} and provides powerful templating logic.
        """
        try:
            system_tpl = self._jinja_env.from_string(template.system)
            user_tpl = self._jinja_env.from_string(template.user)
            
            return {
                "system": system_tpl.render(**variables),
                "user": user_tpl.render(**variables)
            }
        except Exception as e:
            # Captures missing variables (due to StrictUndefined) or Jinja syntax errors
            raise ValueError(f"Error rendering prompt {template.name}: {e}")

    def clear_cache(self):
        """Manually clear the prompt cache (useful for dev/tests)."""
        self._cache.clear()

    def list_versions(self, name: str) -> list[str]:
        """List available versions for a given prompt name."""
        if not self.prompts_dir.exists():
            return []
            
        versions = []
        for version_dir in self.prompts_dir.iterdir():
            if version_dir.is_dir():
                prompt_file = version_dir / f"{name}.yaml"
                if prompt_file.exists():
                    versions.append(version_dir.name)
        
        return sorted(versions)

# Singleton instance for app-wide use
registry = PromptRegistry()
