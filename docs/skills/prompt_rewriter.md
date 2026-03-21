# Prompt Token Rewriter

**Domain:** `optimization`
**Skill ID:** `optimization/prompt_rewriter`

A powerful middleware skill that acts as a deterministic compression logic gate for agents. It ingests a massive, bloated prompt or conversation history and "rewrites" it to use fewer tokens while aggressively retaining 100% of the semantic meaning and instructions.

This is critical for complex agents facing strict token constraints or high LLM API costs.

## Manifest Details

**Parameters Schema:**
*   `raw_text` (string): The bloated, repetitive prompt or extensive conversation history to compress.
*   `compression_aggression` (string): The level of compression: 'low', 'medium', or 'high'.

**Outputs Schema:**
*   `compressed_text` (string): The aggressively shortened prompt retaining semantic constraints.
*   `original_tokens` (integer): The approximate original length.
*   `new_tokens` (integer): The approximate new length.
*   `tokens_saved` (integer): The absolute number of tokens removed.

## Example Usage (Skill Chaining)

The agent invokes this tool automatically when faced with an excessively long context or when instructed to compress a payload. However, you can also use it as a manual middleware step:

```python
from skillware.core.loader import SkillLoader

# 1. Load the middleware
rewriter_bundle = SkillLoader.load_skill("optimization/prompt_rewriter")
rewriter = rewriter_bundle['module'].PromptRewriter()

# 2. Compress a prompt before sending to LLM
result = rewriter.execute({
    "raw_text": "Hello, could you please make sure to read this documentation...",
    "compression_aggression": "high"
})

print(f"Compressed: {result['compressed_text']}")
# Output: "read documentation..."
```

## Maintenance

To run tests specifically for this skill:
```bash
pytest tests/skills/optimization/test_prompt_rewriter.py
```
