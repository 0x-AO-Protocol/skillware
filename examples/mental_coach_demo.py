"""
Example Usage: Mental Coach Local Execute
=========================================

Demonstrates direct execution of the wellness/mental_coach skill without an
LLM agent loop. The skill returns grounded context for a parent agent to use.
"""

from skillware.core.loader import SkillLoader


def main():
    bundle = SkillLoader.load_skill("wellness/mental_coach")
    skill = bundle["module"].MentalCoachSkill()

    scenarios = [
        {
            "label": "Coaching",
            "params": {
                "user_prompt": "I feel stressed at work and need practical coping ideas.",
                "user_jurisdiction": "US",
                "session_mode": "coaching",
                "run_evaluator": False,
            },
        },
        {
            "label": "Crisis escalation",
            "params": {
                "user_prompt": "I want to hurt myself and I am not safe right now.",
                "run_evaluator": False,
            },
        },
        {
            "label": "Blocked clinical request",
            "params": {
                "user_prompt": "Can you diagnose whether I have depression?",
                "run_evaluator": False,
            },
        },
    ]

    for scenario in scenarios:
        print(f"\n=== {scenario['label']} ===")
        result = skill.execute(scenario["params"])
        print("policy_status:", result.get("policy_status"))
        print("scope:", result.get("scope"))
        print("retrieved_sections:", result.get("retrieved_sections", [])[:3])
        print("final_context_for_agent:", result.get("final_context_for_agent", "")[:400], "...")


if __name__ == "__main__":
    main()
