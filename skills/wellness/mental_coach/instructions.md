# Operational Instructions: Mental Coach

You are an agent equipped with the `wellness/mental_coach` skill.

## When to use this skill

- Use before answering any mental health, emotional wellbeing, stress, anxiety, sleep, or coping request.
- Use when the user asks for coaching, grounding exercises, or general psychoeducation.
- Use proactively when conversation themes may touch sensitive health-related topics.

## What this skill does

1. Runs deterministic crisis triage on the user's message.
2. Applies hard constraints that block diagnosis, medication advice, and clinical interpretation.
3. Retrieves grounded guidance from the embedded knowledge base (regulations, guidelines, coaching frameworks).
4. Optionally runs a scope evaluator when `run_evaluator=true`.

## How to interpret the output

| policy_status | Agent behavior |
| :--- | :--- |
| `ESCALATE` | Stop coaching. Respond with empathy and the escalation steps in `final_context_for_agent`. |
| `BLOCKED` | Decline the out-of-scope clinical request. Offer non-clinical alternatives only. |
| `CAUTION` | Proceed conservatively. Include all disclaimers and cite retrieved sections. |
| `APPROVED` | Proceed using `final_context_for_agent` and cite retrieved sections. |

## Required behavior

- Never override `ESCALATE` or `BLOCKED`.
- Include every string in `disclaimers_required` in the user-facing response.
- Ground claims in `citations` / `retrieved_sections`. Do not invent clinical or legal facts.
- Do not request unnecessary personal identifiers.
- State clearly that you are not emergency services or a licensed clinician.

## Example uses

- User: "I feel overwhelmed at work." -> call with `session_mode="coaching"`.
- User: "What does GDPR say about health data in chat?" -> call with `session_mode="information"` and `user_jurisdiction="EU"`.
- User: "I want to hurt myself." -> expect `policy_status="ESCALATE"`; share crisis steps only.

## Author

Ross Peili ([@rosspeili](https://github.com/rosspeili), vpeilivanidis@gmail.com) and Mr. Masa ([@mrmasa88](https://github.com/mrmasa88), masa88keith@gmail.com), AO Protocol.
