# MiCA Module Skill

**ID**: `compliance/mica_module`
**Issuer**: [@rosspeili](https://github.com/rosspeili) ([@ARPAHLS](https://github.com/ARPAHLS))

A highly specialized, localized RAG (Retrieval-Augmented Generation) and policy enforcement engine for the Markets in Crypto-Assets (MiCA) regulation. It ensures any agent using it can understand, query, and enforce the entirety of MiCA with granular precision, acting as a strict compliance firewall.

## Capabilities

*   **Self-Contained Local RAG**: Ships with the full MiCA regulation mapped into a structured `mica_corpus.json` file. It relies on a fast semantic router to prevent overwhelming the parent agent's context window.
*   **Incremental Fetching**: Only pulls precisely the Articles and legal text necessary based on the User's query intent.
*   **Optional Model Swappable Evaluator**: Includes a built-in evaluation loop to review the context and score potential responses for regulatory holes. This node operates entirely independently and the model can be dynamically swapped based on user preference.
*   **Policy Firewall**: Evaluates intent against the regulation before the parent agent generates an external answer, labeling requests as `APPROVED`, `CAUTION`, or `HIGH_RISK_DETECTED`.

## Internal Architecture

The skill is self-contained in `skills/compliance/mica_module/`.

### 1. The Mind (`instructions.md`)
The system prompt teaches the main Agent to:
*   Use a **Pure Cognitive Workflow**: The agent recognizes the MiCA skill via its manifest and determines when statutory context is needed.
*   Formatting: Invokes the skill via a JSON block in the dialogue stream.
*   **Traceability**: Explicitly cites the Article numbers (e.g., Article 59) found in the RAG context.

### 2. The Body (`skill.py` & `mica_corpus.json`)
*   **In-Memory Caching**: The 1MB corpus is cached on the first run, delivering subsequent RAG lookups in **~1.7ms**.
*   **Weighted Surgical Router**: Instead of a "shotgun" match, the router uses a weighted scoring system (Mentions > Keywords > collisions) and throttles retrieval to the **Top 10** most relevant Articles to prevent context window asphyxiation.

## Environment

| Variable | Required | Purpose |
| :--- | :--- | :--- |
| `GOOGLE_API_KEY` | Yes (evaluator / Gemini paths) | Google Generative AI used by the built-in evaluator and RAG flows |

Configure values per [API keys for skills](../usage/api_keys.md).

## Integration & Configuration

This skill is designed for high-performance agentic loops without relying on opaque native tool APIs. 

### Pure Cognitive Integration

This is the recommended pattern for Gemini, Claude, and Llama agents:

1.  **Inject Manifest**: Pass the `manifest.yaml` and `instructions.md` as text into the System Prompt.
2.  **Streaming Loop**: Enable streaming to observe the agent's "Thinking" turn as it identifies the need for RAG.
3.  **Local Execution**: When the agent outputs the skill JSON, execute `mica_skill.execute()` locally and feed the results back to the agent.

### Swapping Evaluator Models

You can dynamically swap the internal evaluator model to another supported target using the `evaluator_model` parameter.

```python
from skillware.core.loader import SkillLoader

# 1. Load the Skill
skill_bundle = SkillLoader.load_skill("compliance/mica_module")
MiCAModuleSkill = skill_bundle['module'].MiCAModuleSkill

# 2. Initialize
validator = MiCAModuleSkill()

# 3. Execute - With the Optional Evaluator Swapped Out!
result = validator.execute({
    "user_prompt": "Can I issue a stablecoin backed by physical art under an e-money license?",
    
    # ---------------------------------------------
    # Evaluator Engine Configuration Options
    # ---------------------------------------------
    "run_evaluator": True,                           # Enable the built-in grading loop
    "evaluator_model": "gemini-1.5-pro-latest"       # Swap out the default flash-lite model!
})

# Access Policy Results
print(f"Status: {result['policy_status']}")
if result['policy_status'] == 'HIGH_RISK_DETECTED':
    print(f"Holes: {result['gemini_evaluator_feedback']['holes_found']}")
```

## Data Schema Output

The skill returns a strictly formatted JSON context block that Parent Agents incorporate sequentially into their memory.

```json
{
  "retrieved_sections": [
    "Title III | Article 16: Authorization requirements"
  ],
  "policy_status": "HIGH_RISK_DETECTED",
  "gemini_evaluator_feedback": {
    "grade": "B-",
    "holes_found": "The setup failed to mention the absolute requirement of publishing a white paper.",
    "suggestion": "Revise the answer to explicitly state that an e-money license is insufficient without a crypto-asset white paper."
  },
  "final_context_for_agent": "Output the revised answer integrating the following requirement: [White paper publication under Article 16]."
}
```

---

## Enterprise disclaimer

This skill is provided for demonstration and integration purposes. It is intended as a starting point that you can adapt to your own data, schemas, and operational requirements. For an enterprise-grade version of this skill with dedicated support, SLAs, and customization, contact skills@arpacorp.net.
