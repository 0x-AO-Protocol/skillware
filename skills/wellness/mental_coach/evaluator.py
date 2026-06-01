"""Optional LLM scope evaluator for mental coach responses."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

try:
    import google.genai as genai
    from google.genai import types
except ImportError:  # pragma: no cover - optional at runtime
    genai = None
    types = None


def run_scope_evaluator(
    user_prompt: str,
    context_text: str,
    disclaimers: list,
    model_name: str = "gemini-2.5-flash-lite",
) -> Dict[str, Any]:
    """Audit a draft coaching response plan against retrieved guidance."""
    disabled_feedback = {
        "grade": "N/A",
        "holes_found": "Evaluator disabled. Review retrieved guidance manually.",
        "suggestion": "Follow retrieved chunks and required disclaimers exactly.",
    }

    if genai is None or types is None:
        return {
            "policy_status": "CAUTION",
            "evaluator_feedback": {
                **disabled_feedback,
                "holes_found": "google-genai is not installed.",
            },
            "final_context_for_agent": _default_context(context_text, disclaimers),
        }

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "policy_status": "CAUTION",
            "evaluator_feedback": {
                **disabled_feedback,
                "holes_found": "GOOGLE_API_KEY is not configured.",
            },
            "final_context_for_agent": _default_context(context_text, disclaimers),
        }

    prompt_payload = f"""
You are a mental wellness scope evaluator. Review whether a parent agent's planned
coaching response would stay within psychoeducation and coaching boundaries.

User query:
{user_prompt}

Retrieved grounding context:
{context_text}

Required disclaimers:
{json.dumps(disclaimers, ensure_ascii=True)}

Flag clinical overreach, missing disclaimers, unsourced claims, or underreaction
to crisis themes. Return JSON only with this schema:
{{
  "policy_status": "APPROVED|CAUTION|BLOCKED",
  "evaluator_feedback": {{
    "grade": "A to F",
    "holes_found": "issues found or none",
    "suggestion": "how the agent should revise its answer"
  }},
  "final_context_for_agent": "instructions for the parent agent"
}}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_payload,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        parsed = json.loads(response.text)
        if "final_context_for_agent" not in parsed:
            parsed["final_context_for_agent"] = _default_context(
                context_text, disclaimers
            )
        return parsed
    except Exception as exc:
        return {
            "policy_status": "CAUTION",
            "evaluator_feedback": {
                "grade": "N/A",
                "holes_found": f"Evaluator API failed: {str(exc)}",
                "suggestion": "Proceed manually using retrieved guidance only.",
            },
            "final_context_for_agent": _default_context(context_text, disclaimers),
        }


def _default_context(context_text: str, disclaimers: list) -> str:
    disclaimer_block = "\n".join(f"- {line}" for line in disclaimers)
    return (
        "Provide supportive coaching using ONLY the retrieved guidance below. "
        "Do not diagnose, prescribe, or interpret clinical records.\n\n"
        f"Required disclaimers:\n{disclaimer_block}\n\n"
        f"Retrieved guidance:\n{context_text}"
    )
