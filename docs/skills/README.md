# 📚 Skill Library

Welcome to the official catalog of Skillware capabilities.

### Office
Skills for document processing, email automation, and productivity.

| Skill | ID | Description |
| :--- | :--- | :--- |
| **[PDF Form Filler](pdf_form_filler.md)** | `office/pdf_form_filler` | Fills AcroForm-based PDFs by mapping user instructions to detected form fields using LLM-based semantic understanding. |

## Finance
Tools for financial analysis, blockchain interaction, and regulatory compliance.

| Skill | ID | Description |
| :--- | :--- | :--- |
| **[Wallet Screening](wallet_screening.md)** | `finance/wallet_screening` | Comprehensive risk assessment for Ethereum wallets. Checks sanctions lists (OFAC, FBI) and identifies interactions with malicious contracts (Mixers, Scams). |


---

## 📥 Installing Skills

Skills are included in the `skillware/skills` directory. To use them:

```python
from skillware.core.loader import SkillLoader

# Load by ID (path relative to skills dir)
skill = SkillLoader.load_skill("finance/wallet_screening")
```
