# Business Diagnostic

**Domain:** `monitoring`
**Skill ID:** `monitoring/business_diagnostic`
**Issuer:** [@mrmasa88](https://github.com/mrmasa88) ([AO](https://github.com/0x-AO-Protocol))
<!-- skill-doc-meta:begin -->
**Version**: `0.1.0` — 8 Sep 2026
<!-- skill-doc-meta:end -->
**Recommended install:** `pip install "skillware[monitoring_business_diagnostic]"`. See [Install extras](../usage/install_extras.md).

[Skill Library](README.md) · [Testing](../TESTING.md)

Deterministic **scenario ledger and calibration**: `{action, as_of, framework, marks, observations?, outcome?, marks_history?}` → `scenarios[]` + `calibration`. An operator-maintained framework (scenarios with an adjudication date, leading indicators with declared per-scenario weights) and the operator's probability marks are evaluated against dated indicator observations. `adjudicate` returns the model-implied probability of each scenario under the declared weights, its delta from the marks, which indicators fired, the next re-mark due date, and days to adjudication. `calibrate` returns Brier scores once an outcome is resolved. Strict checks on every input, a closed error registry, and one honest state (`insufficient_data` with a reason code). `execute()` is a pure function: no network, no clock, no side effects, identical input → identical output. Interface agreed in [issue #338](https://github.com/ARPAHLS/skillware/issues/338).

Where [`monitoring/kpi_gate`](kpi_gate.md) answers "did this period breach a rule?", this skill answers "across periods, which way has the balance of plausibility shifted, and how well calibrated were the operator's marks?". It is a **ledger, not a data source**: observations are recorded upstream by the host or the operator; the skill never collects them, never estimates an unobserved indicator, and never re-marks on the operator's behalf.

> **Skill chains:** Stateless and terminal in v0.1 — marks, observations, history, and outcome travel in the input and come back in the output. Run after the host records an observation; see [Skill chaining](../usage/skill_chaining.md).

## Three terms

- **Operator marks** — the probabilities the operator assigned on `marked_on`. Never overwritten.
- **Model-implied** — what the declared weights imply once observations are applied to the marks. Not a forecast and not a recommendation; always shown next to the operator marks, never in place of them.
- **insufficient_data** — the honest state: a computation the skill refuses to fake, with a reason code from a closed set.

## Design split

- **The framework is operator-owned, versioned, and strict-schema.** Scenario ids and indicator ids are closed sets declared by the framework; the skill ships no scenarios or indicators of its own.
- **The skill's closed error registry covers contract violations only** (schema failures, undeclared ids, marks that do not sum to 1, malformed or out-of-order dates). These codes are the skill's identity and never change per operator.
- **Unobserved indicators contribute 0; nothing is estimated.** With `exhaustive: true` the model-implied values are renormalized to sum to 1; with `false` each scenario updates independently.
- **The evaluation date is an input** (`as_of`). The skill never reads the clock, so staleness and days to adjudication are reproducible offline.

## Agent-loop contract

- Surface `scenarios[].delta` and `scenarios[].fired` next to `operator_mark`; never present `model_implied` on its own
- `marks_stale: true` → prompt the operator to re-mark; never re-mark for them
- `insufficient_data` non-empty → report the reason; the host must not substitute, estimate, or backfill
- Top-level booleans for chain conditions: `fired_any`, `marks_stale`, `insufficient`

## Arithmetic (v0.1)

- Observation signal `o_i`: `yes` → +1, `no` → −1, unobserved → 0.
- For each scenario *s*: `logit(p_s') = logit(p_s) + Σ_i w_{i,s} · o_i`, where `w_{i,s}` is `indicators[i].strengthens[s]` (undeclared → 0).
- `exhaustive: true` → divide every `p_s'` by their sum; `false` → independent update.
- `model_implied` and `delta` are rounded to 3 decimals after normalization.
- `Brier = Σ_s (p_s − y_s)²` with `y_s = 1` for the resolved scenario, 3 decimals; `brier_trend` scores each `marks_history` set in ascending `marked_on` order.

## Validation order (fail-closed, deterministic)

The first contract violation found is returned: request envelope → `action` → `as_of` → framework shape → `strengthens` ids → marks (shape, undeclared ids, missing ids, range, sum) → observations (shape, undeclared ids, duplicates, dates) → outcome → `marks_history`.

## Bundle layout

The skill lives in `skills/monitoring/business_diagnostic/`. [Skill anatomy](../introduction.md#skill-anatomy). **Contract** — see Manifest Details below. **Assurance** — `test_skill.py` in the bundle.

### Effect (`skill.py`)

Pure Python evaluation: fail-closed validation in the order above, closed error registry, logit-space update, optional renormalization, Brier scoring. Standard library only; no clock, no network.

### Directive (`instructions.md`)

Registry ID, the three terms, agent-loop contract (deltas next to marks, re-mark prompts, `insufficient_data` never backfilled), when to invoke, and how to read completed runs vs contract errors.

### Reference (`schemas/`)

JSON Schemas for `framework`, `marks`, `observations`, `outcome`, and the `output` shape (documentation; runtime uses explicit stdlib checks). In-bundle `fixtures/` hold the end-to-end example and one minimal input per error code.

### Corpus (`kb/`)

Synthetic demo framework (`demo_scenarios.json`, timestamped and sourced): four scenarios and two indicators, identical to the end-to-end fixture.

## Manifest Details

**Parameters Schema:**
* `action` (string, required): `adjudicate` or `calibrate`.
* `as_of` (string, required): evaluation date `YYYY-MM-DD` supplied by the host.
* `framework` (object, required): `schema_version: 1`, `framework_id`, `adjudication_date`, `exhaustive`, `scenarios[]` (`id`, `label`, `criterion`), `indicators[]` (`id`, `label`, `strengthens` map). Ids match `^[A-Z][A-Z0-9_]*$`.
* `marks` (object, required): `marked_on`, `remark_every_days`, `values` covering every scenario, each in `[0.001, 0.999]`, summing to 1.
* `observations` (array, optional for `adjudicate`): `indicator`, `observed` (`yes` / `no`), `on`, optional `source`. One entry per indicator; `on` must be after `marked_on` and not after `adjudication_date`.
* `outcome` (object or null, required for `calibrate`): `resolved_on`, `scenario`.
* `marks_history` (array, optional for `calibrate`): earlier mark sets, same shape as `marks`.

Reference JSON Schemas ship under the bundle's `schemas/` directory. The skill enforces the same constraints with explicit stdlib checks (`requirements: []` is deliberate; no runtime `jsonschema` dependency).

**Outputs Schema:**
* `status` (string): `completed` for an evaluation run; `error` for a contract violation.
* `framework_id` (string), `as_of` (string): echoed from the input.
* `scenarios` (array): per declared scenario in declaration order — `id`, `operator_mark`, `fired`; for `adjudicate` also `model_implied` and `delta` (3 decimals, or `null` under `insufficient_data`).
* `calibration` (object): `next_remark_due`, `days_to_adjudication`, `brier` (`null` for `adjudicate`); for `calibrate` also `brier_trend` (array or `null`).
* `fired_any`, `marks_stale`, `insufficient` (boolean); `insufficient_data` (array of `reason` + `detail`).

Contract violations return `{"status": "error", "error": {"code", "detail"}}` instead — errors and the honest state never mix.

**Error registry (closed):** `INVALID_REQUEST`, `UNKNOWN_ACTION`, `INVALID_AS_OF`, `INVALID_FRAMEWORK_SCHEMA`, `INVALID_MARKS_SCHEMA`, `INVALID_OBSERVATIONS_SCHEMA`, `INVALID_OUTCOME_SCHEMA`, `UNKNOWN_SCENARIO_ID`, `UNKNOWN_INDICATOR_ID`, `DUPLICATE_OBSERVATION`, `MARK_OUT_OF_RANGE`, `MARKS_NOT_NORMALIZED`, `OBSERVATION_PREDATES_MARKS`, `OBSERVATION_AFTER_ADJUDICATION`.

**Honest state (closed):** `adjudication_date_passed` — `adjudicate` with `as_of` on or after `adjudication_date` returns the marks with `model_implied: null` and `delta: null`.

## Environment

No environment variables. Fully offline; all inputs are passed to `execute()`.

## Example Usage (Direct)

The bundle ships the end-to-end example from #338 with `as_of` added (`fixtures/example_adjudicate_params.json`, `fixtures/example_calibrate_params.json`, `kb/demo_scenarios.json` — all values synthetic):

```python
import json
import os

from skillware.core.loader import SkillLoader

bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
skill = bundle["class"]()
root = os.path.join("skills", "monitoring", "business_diagnostic", "fixtures")

with open(os.path.join(root, "example_adjudicate_params.json")) as f:
    params = json.load(f)

result = skill.execute(params)
print(result["status"], result["framework_id"], result["as_of"])
for row in result["scenarios"]:
    print(row["id"], row["operator_mark"], row["model_implied"], row["delta"], row["fired"])
print(result["calibration"], result["marks_stale"])
```

Expected: A 0.307 (+0.157), B 0.314 (−0.136), C 0.284 (−0.016), D 0.095 (−0.005), `fired: ["I01"]` on A and B, `next_remark_due 2026-10-16`, `days_to_adjudication 485`. The calibrate fixture (outcome B) returns `brier: 0.425`.

## Usage Examples

Guides: [Usage index](../usage/README.md) · [Agent loops](../usage/agent_loops.md). No skill-specific API keys.

Use `bundle["class"]()` in the snippets below; explicit `bundle["module"].BusinessDiagnosticSkill()` also works.

Sample user message: *Update the launch scenario ledger with this week's observation and tell me which way the balance moved.*

The provider snippets share this compact two-scenario setup:

```python
FRAMEWORK = {
    "schema_version": 1,
    "framework_id": "launch_demo",
    "adjudication_date": "2027-12-31",
    "exhaustive": True,
    "scenarios": [
        {"id": "A", "label": "launch", "criterion": "Launch before the adjudication date."},
        {"id": "B", "label": "no launch", "criterion": "No launch before the adjudication date."},
    ],
    "indicators": [
        {"id": "I01", "label": "design document published", "strengthens": {"A": 1.0, "B": -1.0}}
    ],
}
MARKS = {"marked_on": "2026-07-18", "remark_every_days": 90, "values": {"A": 0.4, "B": 0.6}}
OBSERVATIONS = [{"indicator": "I01", "observed": "yes", "on": "2026-08-20"}]
USER_MESSAGE = (
    "Adjudicate this scenario ledger with the business diagnostic tool as of 2026-09-02. "
    f"framework={FRAMEWORK} marks={MARKS} observations={OBSERVATIONS}"
)
```

### Runnable examples

- Local execute: [`examples/business_diagnostic_demo.py`](../../examples/business_diagnostic_demo.py) — runs the in-bundle fixtures fully offline: adjudicate, calibrate, and one fail-closed contract error

### Gemini

```python
import google.genai as genai
from google.genai import types
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
skill = bundle["class"]()
client = genai.Client()
gemini_tool = SkillLoader.to_gemini_tool(bundle)
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=USER_MESSAGE,
    config=types.GenerateContentConfig(
        tools=[gemini_tool],
        system_instruction=bundle["instructions"],
    ),
)
for part in response.candidates[0].content.parts:
    if part.function_call:
        result = skill.execute(dict(part.function_call.args))
        print(result["status"], result["scenarios"])
```

### Claude

```python
import os

import anthropic
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
skill = bundle["class"]()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
tools = [SkillLoader.to_claude_tool(bundle)]
response = client.messages.create(
    model="claude-3-5-haiku-latest",
    max_tokens=1024,
    system=bundle["instructions"],
    tools=tools,
    messages=[{"role": "user", "content": USER_MESSAGE}],
)
for block in response.content:
    if block.type == "tool_use":
        result = skill.execute(dict(block.input))
        print(result["status"], result["scenarios"])
```

### OpenAI

```python
import json
import os

from openai import OpenAI
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
skill = bundle["class"]()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
tool = SkillLoader.to_openai_tool(bundle)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": bundle["instructions"]},
        {"role": "user", "content": USER_MESSAGE},
    ],
    tools=[tool],
)
message = response.choices[0].message
if message.tool_calls:
    args = json.loads(message.tool_calls[0].function.arguments)
    result = skill.execute(args)
    print(result["status"], result["scenarios"])
```

### DeepSeek

```python
import json
import os

from openai import OpenAI
from skillware.core.env import load_env_file
from skillware.core.loader import SkillLoader

load_env_file()
bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
skill = bundle["class"]()
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
tool = SkillLoader.to_deepseek_tool(bundle)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": bundle["instructions"]},
        {"role": "user", "content": USER_MESSAGE},
    ],
    tools=[tool],
)
message = response.choices[0].message
if message.tool_calls:
    args = json.loads(message.tool_calls[0].function.arguments)
    result = skill.execute(args)
    print(result["status"], result["scenarios"])
```

### Ollama (prompt mode)

```python
import json

from skillware.core.loader import SkillLoader

bundle = SkillLoader.load_skill("monitoring/business_diagnostic")
skill = bundle["class"]()
prompt = (
    "You may call tools as JSON blocks.\n"
    f"Tool: {bundle['manifest']['name']}\n"
    f"Instructions:\n{bundle['instructions']}\n"
    f"User: {USER_MESSAGE}"
)
print(prompt)
# When the model emits JSON tool args, pass them to execute:
result = skill.execute(
    {
        "action": "adjudicate",
        "as_of": "2026-09-02",
        "framework": FRAMEWORK,
        "marks": MARKS,
        "observations": OBSERVATIONS,
    }
)
print(json.dumps(result, indent=2))
```

## Limitations (v0.1)

- **No data acquisition**: observations are recorded upstream; the skill never fetches, scrapes, or polls anything.
- **No estimation**: an unobserved indicator contributes 0; nothing is imputed.
- **No re-marking**: `marks_stale` prompts the operator; the skill never writes marks.
- **No weight tuning**: `strengthens` weights come from the framework; the skill never adjusts them.
- One observation per indicator per call; the host de-duplicates before calling.

v0.1 is the ledger; projections against declared targets and a report skeleton are planned as Skill Upgrades.

---

<!-- skill-history:begin -->
## Skill history

Commits that touched this skill bundle or its catalog page ([`monitoring/business_diagnostic`](https://github.com/ARPAHLS/skillware/tree/main/skills/monitoring/business_diagnostic)).

| Commit | Description | Date | Version | Contributors |
| :--- | :--- | :--- | :--- | :--- |
| *(pending merge)* | Add monitoring/business_diagnostic v0.1.0 — scenario ledger and calibration (#338) | 8 Sep 2026 | `0.1.0` | [@mrmasa88](https://github.com/mrmasa88) |
<!-- skill-history:end -->

## Enterprise disclaimer

This skill is provided for demonstration and integration purposes. It is intended as a starting point that you can adapt to your own scenarios, indicators, and operational requirements. For an enterprise-grade version of this skill with dedicated support, SLAs, and customization, contact skills@arpacorp.net.
