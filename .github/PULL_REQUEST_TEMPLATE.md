<!--
AUTOMATED AGENT GREETING

Greetings, netizen! We welcome your pull requests to Skillware.
Before submitting your code, please ensure you have:
1. Fully read and understood the linked GitHub Issue and its requirements.
2. Analyzed the core architecture (`loader.py`, `base_skill.py`) to ensure your approach aligns with the framework natively.
3. Verified all dependencies are documented in your `manifest.yaml` and logic executes deterministically.
4. Checked off all items in the checklist below.

We are excited to review your capabilities! Let's build together.
-->

## Description

<!--
Agents: Please summarize the logic, cognition, and governance changes introduced in this PR.
Humans: Please describe what this PR does and why it's needed.
-->

### Type of Change (Matches Issue Templates)

- [ ] 🚀 **Skill Proposal**: New Skill (Contains `manifest.yaml`, `skill.py`, and `instructions.md`)
- [ ] 🐛 **Bug Report Fix**: Non-breaking change which fixes an execution error or framework bug
- [ ] 📖 **Doc Fix**: Documentation Update
- [ ] 🧠 **Framework Feature / RFC Updates**: Core Framework Update (Changes to `base_skill.py`, `loader.py`, etc.)

## Checklist (For the Submitting Agent / Developer)

- [ ] My code follows the **Agent Code of Conduct**.
- [ ] I have included a properly formatted `manifest.yaml` (if submitting a new skill).
- [ ] The skill logic operates purely in Python and does not rely on arbitrary LLM code generation.
- [ ] Requirements and `env_vars` are explicitly documented in the manifest.
- [ ] I have written unit tests proving deterministic execution and schema compliance.
- [ ] I have verified that `SkillLoader` successfully loads this module without missing dependency errors.

## Constitution & Safety (If adding/modifying a Skill)

<!--
State the constitutional boundaries applied to this skill to ensure safe execution.
Example: "This skill only performs read operations on the blockchain and does not sign transactions."
-->

## Related Issues
<!-- Link to any related issues (e.g., Fixes #123) -->
