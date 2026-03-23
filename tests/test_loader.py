import pytest
from skillware.core.loader import SkillLoader

def test_load_skill_not_found():
    with pytest.raises(FileNotFoundError):
        SkillLoader.load_skill("nonexistent_skill_path_12345")

def test_to_ollama_prompt():
    dummy_bundle = {
        "manifest": {
            "name": "test_ollama_skill",
            "description": "A very useful test skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": "The first arg"}
                },
                "required": ["arg1"]
            }
        }
    }
    
    prompt = SkillLoader.to_ollama_prompt(dummy_bundle)
    assert "### Tool: `test_ollama_skill`" in prompt
    assert "**Description:** A very useful test skill." in prompt
    assert "- `arg1` (string): The first arg [Required]" in prompt

def test_to_gemini_tool():
    dummy_bundle = {
        "manifest": {
            "name": "test_gemini_skill",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        }
    }
    tool = SkillLoader.to_gemini_tool(dummy_bundle)
    assert tool["name"] == "test_gemini_skill"
    # Gemini requires UPPERCASE types for Protobufs
    assert tool["parameters"]["type"] == "OBJECT"
    assert tool["parameters"]["properties"]["param1"]["type"] == "STRING"

def test_to_claude_tool():
    dummy_bundle = {
        "manifest": {
            "name": "test_claude_skill",
            "description": "desc",
            "parameters": {
                "type": "object",
                "properties": {"arg_claude": {"type": "string"}}
            }
        }
    }
    tool = SkillLoader.to_claude_tool(dummy_bundle)
    assert tool["name"] == "test_claude_skill"
    assert tool["input_schema"]["type"] == "object"
