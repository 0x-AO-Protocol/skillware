"""Deterministic hard-constraint evaluation for mental coach requests."""

from __future__ import annotations

import importlib.util
import os
import re
from typing import Any, Dict, List

SEVERITY_ORDER = {"block": 0, "escalate": 1, "caution": 2}


def _load_hard_constraints():
    try:
        from .kb_loader import load_hard_constraints as loader

        return loader()
    except ImportError:
        kb_loader_path = os.path.join(os.path.dirname(__file__), "kb_loader.py")
        spec = importlib.util.spec_from_file_location(
            "mental_coach_kb_loader", kb_loader_path
        )
        if spec is None or spec.loader is None:
            return {}
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.load_hard_constraints()


def evaluate_constraints(user_prompt: str) -> Dict[str, Any]:
    """Return constraint hits and the strongest resulting action."""
    config = _load_hard_constraints()
    rules = config.get("constraints", [])
    prompt_lower = (user_prompt or "").lower()
    hits: List[Dict[str, str]] = []

    for rule in rules:
        rule_id = rule.get("id", "unknown")
        severity = (rule.get("severity") or "caution").lower()
        patterns = rule.get("patterns") or []
        for pattern in patterns:
            try:
                if re.search(pattern, prompt_lower, flags=re.IGNORECASE):
                    hits.append(
                        {
                            "id": rule_id,
                            "severity": severity,
                            "label": rule.get("label", rule_id),
                            "message": (rule.get("message") or "").strip(),
                        }
                    )
                    break
            except re.error:
                continue

    if not hits:
        return {
            "action": "continue",
            "hits": [],
            "messages": [],
        }

    strongest = min(hits, key=lambda item: SEVERITY_ORDER.get(item["severity"], 99))
    action_map = {
        "block": "blocked",
        "escalate": "escalate",
        "caution": "caution",
    }
    return {
        "action": action_map.get(strongest["severity"], "caution"),
        "hits": hits,
        "messages": [item["message"] for item in hits if item.get("message")],
    }


def required_disclaimers(session_mode: str) -> List[str]:
    config = _load_hard_constraints()
    disclaimers = config.get("disclaimers", {})
    combined: List[str] = []
    for key in ("default", session_mode):
        for line in disclaimers.get(key, []) or []:
            cleaned = str(line).strip()
            if cleaned and cleaned not in combined:
                combined.append(cleaned)
    return combined
