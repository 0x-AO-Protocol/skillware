import pytest
from skillware.core.loader import SkillLoader

def test_synthetic_generator_manifest():
    bundle = SkillLoader.load_skill("data_engineering/synthetic_generator")
    assert bundle["manifest"]["name"] == "data_engineering/synthetic_generator"
    assert "entropy_temperature" in bundle["manifest"]["parameters"]['properties']

def test_entropy_score():
    bundle = SkillLoader.load_skill("data_engineering/synthetic_generator")
    skill_class = bundle["module"].SyntheticGeneratorSkill
    skill = skill_class()

    # Highly repetitive, low entropy
    low_entropy_text = "test " * 100
    score_low = skill._calculate_entropy_score(low_entropy_text)

    # More diverse, higher entropy
    high_entropy_text = "The quick brown fox jumps over the lazy dog. Programming is fun! Diverse sentences."
    score_high = skill._calculate_entropy_score(high_entropy_text)

    assert score_high > score_low

def test_execute_success(mocker):
    bundle = SkillLoader.load_skill("data_engineering/synthetic_generator")
    skill = bundle["module"].SyntheticGeneratorSkill()

    mock_json_response = '''```json
[
  {"instruction": "do this", "input": "input data", "output": "output data"}
]
```'''

    # Mock the gemini call to avoid hitting realistic endpoints
    mocker.patch.object(skill, '_call_gemini', return_value=mock_json_response)

    result = skill.execute({
        "domain": "test domain",
        "num_samples": 1,
        "diversity_prompt": "be diverse",
        "model_provider": "gemini"
    })

    assert result["status"] == "success"
    assert result["provider_used"] == "gemini"
    assert result["samples_generated"] == 1
    assert "samples" in result
    assert result["samples"][0]["instruction"] == "do this"
