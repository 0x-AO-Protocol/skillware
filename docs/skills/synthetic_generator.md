# Synthetic Data Generator Skill

**Domain:** `data_engineering`
**Skill ID:** `data_engineering/synthetic_generator`

A specialized data engineering capability that combats "model collapse" by generating high-entropy, highly structured synthetic data intentionally designed to fine-tune other models.

## Capabilities

*   **Model Agnosticism**: Supports dynamic internal LLM configuration, letting the user trigger generation via Ollama (local), Google Gemini, or Anthropic Claude.
*   **Combinatorial Entropy Injection**: Designed to explicitly seek out edge-case personas via the `diversity_prompt`, significantly raising the variance of training data.
*   **Zero-Dependency Evaluation Heuristic**: Employs built-in `zlib` string compression ratios to calculate a dynamic entropy score, allowing the coordinating agent to reject low-entropy boilerplate data instantly.

## Internal Architecture

The skill is located in `skillware/skills/data_engineering/synthetic_generator/`.

### 1. The Mind (`instructions.md`)
The system instructions emphasize boundary-pushing data generation. It prohibits standard AI tropes and enforces schema obedience.

### 2. The Body (`skill.py`)
*   **Data Generation**: The skill handles invoking the LLM behind the scenes, using the configured provider and isolating the `temperature` specifically for the data generation task so the primary coordinating agent doesn't need to run at high temperature.
*   **Validation**: Attempts to automatically parse out code blocks to extract standard JSON object arrays.
*   **Entropy Scoring**: Converts text sequences into `zlib` compressed bytes. A poor compression ratio implies high lexical variance (less repetitive syntax).

## Integration Guide

### Environment Variables
Depending on the requested `model_provider`, ensure you have the necessary API key exported:

```bash
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="AIzaSy..."
# Or run an Ollama server locally on default port 11434
```

### Usage (Skillware Loader)

```python
from skillware.core.loader import SkillLoader
import json

# 1. Load the Skill
skill_bundle = SkillLoader.load_skill("data_engineering/synthetic_generator")
SyntheticGeneratorSkill = skill_bundle['module'].SyntheticGeneratorSkill()

# 2. Execute
result = SyntheticGeneratorSkill.execute({
    "domain": "medical_coding_disputes",
    "num_samples": 5,
    "entropy_temperature": 0.9,
    "diversity_prompt": "Ensure edge-case scenarios involving dual-insurance coverage overlaps.",
    "model_provider": "gemini"
})

print(f"Generated {result['samples_generated']} samples with Entropy Score: {result['entropy_score']}")
print(json.dumps(result['samples'], indent=2))
```

## Data Schema

The skill constructs a response validating the pipeline and containing the raw samples.

```json
{
  "samples": [
    {
      "instruction": "Resolve the coding dispute for CPT 99291...",
      "input": "Patient A admitted with BlueCross and Medicare...",
      "output": "Since primary is exhausted..."
    }
  ],
  "entropy_score": 0.88,
  "status": "success",
  "provider_used": "gemini",
  "samples_generated": 1
}
```

## Limitations

*   **Structure Consistency**: If the LLM generates improperly formatted JSON (despite the strict prompt), the parsing step may fail, requiring the agent to retry the skill execution.
*   **Heuristic Entropy**: The `zlib` entropy score evaluates lexical byte-variance, not semantic variance. It serves as a guardrail against robotic boilerplate repetition but is not mathematically bulletproof.
