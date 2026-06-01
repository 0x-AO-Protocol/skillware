# Mental Coach Skill

**ID**: `wellness/mental_coach`
**Issuer**: Ross Peili ([@rosspeili](https://github.com/rosspeili), vpeilivanidis@gmail.com) and Mr. Masa ([@mrmasa88](https://github.com/mrmasa88), masa88keith@gmail.com) · [@AO Protocol](https://github.com/0x-AO-Protocol)

[Skill Library](README.md) · [Testing](../TESTING.md)

A self-contained mental wellness coaching skill with embedded knowledge base, deterministic crisis triage, hard constraint enforcement, and optional scope evaluation. Parent AO Protocol agents call this skill before generating user-facing coaching responses.

## Capabilities

* **Embedded knowledge base**: Ships `kb/corpus.json` (regulations, guidelines, crisis resources, coaching frameworks) and `kb/hard_constraints.yaml` inside the skill module.
* **Crisis triage**: Deterministic pattern matching escalates self-harm, abuse, and immediate-danger signals before coaching continues.
* **Hard constraints**: Blocks diagnosis requests, medication advice, and clinical record interpretation.
* **Grounded retrieval**: Jurisdiction- and session-aware chunk routing with citations for traceable answers.
* **Optional scope evaluator**: When enabled, audits planned responses against retrieved guidance via Gemini.

## Internal Architecture

The skill lives in `skills/wellness/mental_coach/`.

### 1. The Mind (`instructions.md`)

Teaches the parent agent when to invoke the skill, how to interpret `policy_status`, and required disclaimer behavior.

### 2. The Body (`skill.py` + `kb/`)

* `crisis_gate.py` — deterministic crisis detection
* `constraint_engine.py` — hard rule evaluation
* `kb_loader.py` — corpus cache and weighted retrieval
* `evaluator.py` — optional LLM scope audit

## Environment

| Variable | Required | Purpose |
| :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Only when `run_evaluator=true` | Gemini scope evaluator |

Configure values per [API keys for skills](../usage/api_keys.md).

## Arguments

| Argument | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `user_prompt` | string | Yes | - | User message or coaching request. |
| `user_jurisdiction` | string | No | `unknown` | Jurisdiction hint: US, EU, UK, GLOBAL, unknown. |
| `session_mode` | string | No | `coaching` | coaching, information, or crisis_check. |
| `run_evaluator` | boolean | No | `false` | Run optional Gemini scope audit. |
| `evaluator_model` | string | No | `gemini-2.5-flash-lite` | Evaluator model name. |
| `max_chunks` | integer | No | `8` | Max KB chunks to retrieve (1-15). |

## Usage Examples

Guides: [Usage index](../usage/README.md) · [Agent loops](../usage/agent_loops.md) · [API keys](../usage/api_keys.md).

### Direct execute

```python
from skillware.core.loader import SkillLoader

bundle = SkillLoader.load_skill("wellness/mental_coach")
skill = bundle["module"].MentalCoachSkill()
result = skill.execute(
    {
        "user_prompt": "I feel stressed at work. What coping strategies can help?",
        "user_jurisdiction": "US",
        "session_mode": "coaching",
        "run_evaluator": False,
    }
)
print(result["policy_status"])
print(result["final_context_for_agent"])
```

Sample user message: *I feel overwhelmed at work and need practical coping ideas.*

### Gemini

```python
import google.genai as genai
from google.genai import types
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("wellness/mental_coach")
skill = bundle["module"].MentalCoachSkill()
client = genai.Client()
tool = SkillLoader.to_gemini_tool(bundle)
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="I'm stressed at work and need grounded coping ideas.",
    config=types.GenerateContentConfig(
        tools=[tool],
        system_instruction=bundle["instructions"],
    ),
)
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = skill.execute(dict(part.function_call.args))
        print(result["final_context_for_agent"])
```

### Claude

```python
import os
import anthropic
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("wellness/mental_coach")
skill = bundle["module"].MentalCoachSkill()
tools = [SkillLoader.to_claude_tool(bundle)]
# Full agent loop: see docs/usage/agent_loops.md
```

### OpenAI

```python
import os
from openai import OpenAI
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("wellness/mental_coach")
skill = bundle["module"].MentalCoachSkill()
openai_tool = SkillLoader.to_openai_tool(bundle)
# Match tool_call.function.name (wellness_mental_coach)
```

### DeepSeek

```python
import os
from openai import OpenAI
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("wellness/mental_coach")
skill = bundle["module"].MentalCoachSkill()
deepseek_tool = SkillLoader.to_deepseek_tool(bundle)
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
```

### Ollama

`SkillLoader.to_ollama_prompt(bundle)`; match `"tool": "wellness/mental_coach"`. See [Ollama usage](../usage/ollama.md).

## Data Schema Output

```json
{
  "policy_status": "APPROVED",
  "scope": "coaching",
  "retrieved_sections": [
    "WHO workplace stress guidance (summary) | Managing stress [who-workplace-stress]"
  ],
  "citations": [
    {
      "chunk_id": "who-workplace-stress",
      "source_doc": "WHO workplace stress guidance (summary)",
      "section": "Managing stress",
      "jurisdiction": "GLOBAL"
    }
  ],
  "hard_constraints_applied": [],
  "disclaimers_required": [
    "This is supportive coaching and psychoeducation, not medical advice, diagnosis, or treatment."
  ],
  "evaluator_feedback": {
    "grade": "N/A",
    "holes_found": "Evaluator disabled. Review retrieved guidance manually.",
    "suggestion": "Follow retrieved chunks and required disclaimers exactly."
  },
  "final_context_for_agent": "Provide supportive coaching using ONLY the retrieved guidance below...",
  "privacy_metadata": {
    "jurisdiction": "US",
    "session_mode": "coaching",
    "kb_chunks_retrieved": 2
  }
}
```

---

## Enterprise disclaimer

This skill provides wellness coaching guardrails and psychoeducation support. It is not emergency services, telehealth, or a substitute for licensed professional care. HIPAA/GDPR alignment depends on deployment architecture and operator policies. Co-authored by Ross Peili (vpeilivanidis@gmail.com) and Mr. Masa (masa88keith@gmail.com) for AO Protocol.
