# PDF Form Filler Skill

**ID**: `office/pdf_form_filler`

A productivity skill that fills AcroForm-based PDFs by mapping natural language instructions to detected form fields using semantic understanding.

## 📋 Capabilities

*   **Smart Field Detection**: Automatically identifies text fields, checkboxes, radio buttons, and dropdowns in standard PDFs.
*   **Semantic Mapping**: Uses an internal LLM (Claude) to understand user instructions (e.g., "Sign me up for the newsletter") and map them to the correct field (e.g., `checkbox_subscribe_newsletter`).
*   **Context Awareness**: Extracts nearby text labels to ensure accurate mapping, even if field names are obscure (e.g., `field_123` vs label "First Name").
*   **Type Safety**: Automatically converts values to the correct format (booleans for checkboxes, specific options for dropdowns).

## 📂 Internal Architecture

The skill is self-contained in `skillware/skills/office/pdf_form_filler/`.

### 1. The Mind (`instructions.md`)
The system prompt teaches the internal mapping engine to:
*   Analyze the provided "User Instructions".
*   Review the list of "Detected Fields" (ID, Type, Context, Options).
*   Output a strict JSON mapping of `Field ID -> Value`.
*   Handle ambiguities by preferring precision over guessing.

### 2. The Body (`skill.py` & `utils.py`)
*   **PDF Processing**: Uses `PyMuPDF` (fitz) for high-fidelity rendering and widget manipulation.
*   **LLM Integration**: Wraps the Anthropic SDK to perform the semantic reasoning step.
*   **Validation**: Ensures values match the field type (e.g., selecting a valid option from a dropdown).

## 💻 Integration Guide

### Environment Variables
You must provide an Anthropic API key for the semantic mapping engine.

```bash
ANTHROPIC_API_KEY="sk-ant-..."
```

### Usage (Skillware Loader)

```python
from skillware.core.loader import SkillLoader

# 1. Load the Skill
skill_bundle = SkillLoader.load_skill("office/pdf_form_filler")
PDFFormFillerSkill = skill_bundle['module'].PDFFormFillerSkill

# 2. Initialize
filler = PDFFormFillerSkill()

# 3. Execute
result = filler.execute({
    "pdf_path": "/absolute/path/to/form.pdf",
    "instructions": "Name: John Doe. Check the terms of service box."
})

print(f"Filled PDF saved to: {result['output_path']}")
```

## 📊 Data Schema

The skill returns a JSON object with the result of the operation.

```json
{
  "status": "success",
  "output_path": "/path/to/form_filled.pdf",
  "filled_fields": [
    "page0_full_name",
    "page0_terms_check"
  ],
  "message": "Successfully filled 2 fields."
}
```

## ⚠️ Limitations

*   **AcroForms Only**: Does not support XFA forms or non-interactive "flat" PDFs.
*   **LLM Dependency**: Requires an active internet connection and valid API key for the semantic mapping step.
