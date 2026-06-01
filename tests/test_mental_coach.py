import pytest
from skillware.core.loader import SkillLoader


@pytest.fixture
def mental_coach_skill():
    bundle = SkillLoader.load_skill("wellness/mental_coach")
    skill_class = bundle["module"].MentalCoachSkill
    return skill_class(), bundle


def test_mental_coach_manifest(mental_coach_skill):
    skill, bundle = mental_coach_skill
    assert skill.manifest["name"] == "wellness/mental_coach"
    assert bundle["manifest"]["issuer"]["org"] == "AO Protocol"
    assert "crisis" in bundle["instructions"].lower()


def test_mental_coach_router_stress_match(mental_coach_skill):
    skill, _ = mental_coach_skill
    from skills.wellness.mental_coach.kb_loader import load_corpus, route_and_fetch

    corpus = load_corpus()
    matched = route_and_fetch(
        "I am stressed at work and need breathing exercises",
        corpus,
        jurisdiction="GLOBAL",
        session_mode="coaching",
    )
    assert matched
    assert any("stress" in " ".join(chunk.get("keywords", [])) for chunk in matched)


def test_mental_coach_jurisdiction_filter(mental_coach_skill):
    from skills.wellness.mental_coach.kb_loader import load_corpus, route_and_fetch

    corpus = load_corpus()
    eu_matches = route_and_fetch(
        "gdpr health data consent",
        corpus,
        jurisdiction="EU",
        session_mode="information",
    )
    assert eu_matches
    assert all(
        chunk.get("jurisdiction") in {"EU", "GLOBAL"} for chunk in eu_matches
    )
