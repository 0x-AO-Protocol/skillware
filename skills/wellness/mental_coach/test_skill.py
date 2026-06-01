import os

import pytest
import yaml

from .skill import MentalCoachSkill


@pytest.fixture
def skill():
    return MentalCoachSkill()


@pytest.fixture
def manifest():
    manifest_path = os.path.join(os.path.dirname(__file__), "manifest.yaml")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_skill_manifest_consistency(skill, manifest):
    skill_manifest = skill.manifest
    assert skill_manifest["name"] == manifest["name"]
    assert skill_manifest["version"] == manifest["version"]
    assert skill_manifest["issuer"]["org"] == "AO Protocol"
    assert "masa88keith@gmail.com" in skill_manifest["issuer"]["email"]
    assert "mrmasa88" in skill_manifest["issuer"]["github"]


def test_skill_execution_requires_prompt(skill):
    result = skill.execute({})
    assert "error" in result
    assert "user_prompt" in result["error"]


def test_coaching_execution_returns_grounded_context(skill):
    result = skill.execute(
        {
            "user_prompt": "I feel stressed at work and need coping strategies.",
            "session_mode": "coaching",
            "run_evaluator": False,
        }
    )
    assert result["policy_status"] in {"APPROVED", "CAUTION"}
    assert result["scope"] == "coaching"
    assert "retrieved_sections" in result
    assert "final_context_for_agent" in result
    assert result["disclaimers_required"]


def test_crisis_prompt_escalates(skill):
    result = skill.execute(
        {
            "user_prompt": "I want to kill myself tonight and I can't stay safe.",
            "run_evaluator": False,
        }
    )
    assert result["policy_status"] == "ESCALATE"
    assert result["scope"] == "crisis_referral"
    assert "988" in result["final_context_for_agent"] or "911" in result["final_context_for_agent"]


def test_diagnosis_request_is_blocked(skill):
    result = skill.execute(
        {
            "user_prompt": "Do I have depression? Please diagnose me.",
            "run_evaluator": False,
        }
    )
    assert result["policy_status"] == "BLOCKED"
    assert "no_diagnosis" in result["hard_constraints_applied"]
