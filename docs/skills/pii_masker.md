# PII Masker

**ID**: `compliance/pii_masker`
**Category**: Compliance

High-precision, local PII (Personally Identifiable Information) detection and redaction using the `micro-f1-mask` model. This skill acts as a "Privacy Firewall" at the edge, scrubbing sensitive data before it reaches high-latency cloud models.

> [!WARNING]
> **Disclaimer**: This skill and the underlying base model are provided for **demonstration and proof-of-concept purposes only**. 
> Reaching production-grade 95%+ enterprise accuracy requires architectural optimizations, hard-negative mining, and dataset-specific fine-tuning. Full implementation of the `micro-f1-mask` privacy middleware should only happen after you rigorously fine-tune and test it exclusively with your own proprietary data structures.
> Visit the core project repository for training orchestration and full middleware execution: [github.com/arpahls/micro-f1-mask](https://github.com/arpahls/micro-f1-mask)

## How It Works

Agentic workflows inherently risk leaking sensitive user data (names, physical addresses, emails, crypto wallets, etc.) to external LLM providers. This skill solves this by utilizing a local [Ollama](https://ollama.com/) instance hosting the `arpacorp/micro-f1-mask` edge model. 

1. **Contextual Recognition**: Unlike rigid regex patterns, the 270M parameter model is trained to recognize syntactic structure and distinguish between generic information (e.g. "a specific date") and genuine PII (e.g. "a birth date").
2. **Local Execution**: The text is evaluated entirely on your local node, ensuring that raw unencrypted data never touches the external internet.

## Prerequisites

- **Local Inference Support**: This skill uses the `requests` library to communicate entirely locally.
- **Ollama**: You must have [Ollama](https://ollama.com/) running.
- **Model**: You must pull the base privacy edge model before utilizing this skill:
  ```bash
  ollama run arpacorp/micro-f1-mask
  ```
*(Note for full-cycle setups: While Redis is a strict prerequisite for running the full standalone FastAPI bridge of the `micro-f1-mask` repository, it is **not** a prerequisite for invoking this specific `skillware` skill, as this skill performs the stateless scrubbing pass only.)*

## Integration & Full Cycle Nuances

Currently, this `pii_masker` skill functions primarily as a **Forward-Pass Scrubber** (Phase A). 
When an agent calls this skill on a block of text, the skill returns a sanitized string with identifying markers (e.g., `[PERSON_1]`).

**Stateless Design**: By default, this specific Skillware component is stateless. It performs the LLM call and tokenizes the output, but it *does not* automatically preserve the mapping in a local vault (like Redis). 
For a complete End-to-End Enterprise integration (The "Full Cycle" ➔ Mask ➔ Send to Cloud ➔ Get Response ➔ Unmask), external developers should either:
- **Option A (Full Middleware Proxy):** Stand up the full standalone FastAPI bridge + Redis vault provided at the [micro-f1-mask repo](https://github.com/arpahls/micro-f1-mask) and point the agent's network traffic entirely through it.
- **Option B (Stateful Agent Logic):** Build custom logic within the calling agent that parses the detected entities returned from this skill's `metadata`, preserves them in its own internal session database or memory variables, invokes the cloud API, and strings-replaces the tags back onto the cloud response. For understanding how state/vault recovery works conceptually during this reconstruction phase, review the core project's dedicated [API Reference & Lifecycle Architecture](https://github.com/ARPAHLS/micro-f1-mask/blob/main/docs/API.md).

## Arguments

| Argument | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `text` | string | Yes | - | The raw, sensitive input string. |
| `mode` | string | No | `mask` | Options: `mask` (e.g., `[PERSON]`), `redact` (e.g., `XXXX`), or `remove` (removes the token entirely). |
| `ollama_url` | string | No | `http://localhost:11434` | The URL for your local Ollama instance running the model. |

## Supported Entity Types
The `micro-f1-mask` model detects a variety of entities, including but not limited to:
- Names (`[PERSON]`)
- Emails (`[EMAIL]`)
- Phone Numbers (`[PHONE]`)
- Physical Addresses (`[ADDRESS]`)
- Crypto Wallets (`[CRYPTO_ADDRESS]`)
- Identification Numbers (SSN, Passports, etc.)

## Example Usage

Input text:
```text
Hello John Doe, your wallet 0xabc123 has been verified.
```

JSON Return (mask mode):
```json
{
  "sanitized_text": "Hello [PERSON_1], your wallet [CRYPTO_ADDRESS] has been verified.",
  "metadata": {
    "detected_entities": ["PERSON", "CRYPTO_ADDRESS"],
    "entity_count": 2,
    "security_level": "local-only",
    "model": "arpacorp/micro-f1-mask"
  }
}
```
