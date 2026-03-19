import pytest
from pathlib import Path
from services.llm.prompt_registry import PromptRegistry, PromptTemplate

# Use the real registry instance to test actual prompts
from services.llm.prompt_registry import registry as real_registry

def test_load_real_prompts():
    """Ensure all prompts in the v1 directory are valid and loadable."""
    prompts_dir = Path(__file__).parent.parent.parent / "services" / "llm" / "prompts" / "v1"
    yaml_files = list(prompts_dir.glob("*.yaml"))
    
    assert len(yaml_files) >= 3, "Expected at least 3 core prompts"
    
    for file in yaml_files:
        name = file.stem
        template = real_registry.load_prompt(name, "v1")
        assert isinstance(template, PromptTemplate)
        assert template.name == name
        assert template.version == "v1"
        # Check for Jinja2 variable syntax in either system or user
        assert "{{" in template.system or "{{" in template.user

def test_render_prompt():
    template = real_registry.load_prompt("company_summary", "v1")
    test_val = "UniqueTestString123"
    rendered = real_registry.render_prompt(template, {"website_content": test_val})
    
    # Assert variable substitution instead of hardcoded strings
    assert test_val in rendered["user"]
    assert isinstance(rendered["system"], str)
    assert len(rendered["system"]) > 0

def test_render_missing_variable():
    template = real_registry.load_prompt("company_summary", "v1")
    # Jinja with StrictUndefined raises error on missing vars
    # Match the start of the error message we defined in registry.py
    with pytest.raises(ValueError, match="Error rendering prompt"):
        real_registry.render_prompt(template, {})

def test_custom_registry_path(tmp_path):
    # Create a dummy prompt in a temp dir
    (tmp_path / "v1").mkdir()
    dummy_yaml = """
    version: "v1"
    name: "test_prompt"
    model: "gpt-3.5-turbo"
    temperature: 0.5
    max_tokens: 100
    system: "System {{ var }}"
    user: "User {{ var }}"
    """
    (tmp_path / "v1" / "test_prompt.yaml").write_text(dummy_yaml, encoding="utf-8")
    
    reg = PromptRegistry(prompts_dir=str(tmp_path))
    template = reg.load_prompt("test_prompt", "v1")
    assert template.name == "test_prompt"
    
    rendered = reg.render_prompt(template, {"var": "123"})
    assert rendered["system"] == "System 123"
    assert rendered["user"] == "User 123"

def test_list_versions():
    versions = real_registry.list_versions("company_summary")
    assert "v1" in versions
