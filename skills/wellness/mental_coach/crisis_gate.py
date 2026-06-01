"""Deterministic crisis triage for mental coach requests."""

from __future__ import annotations

import importlib.util
import os
import re
from typing import Any, Dict, List

CRISIS_PATTERNS = [
    {
        "category": "immediate_danger",
        "severity": "escalate",
        "patterns": [
            r"\b(kill myself|end my life|suicide tonight|going to die tonight)\b",
            r"\b(hurt myself right now|cut myself now|overdose tonight)\b",
            r"\b(can't stay safe|not safe right now|about to hurt)\b",
        ],
    },
    {
        "category": "self_harm",
        "severity": "escalate",
        "patterns": [
            r"\b(suicid(e|al)|self[- ]harm|self harm|want to die|don't want to live)\b",
            r"\b(harm myself|hurt myself|cutting myself|end it all)\b",
        ],
    },
    {
        "category": "abuse",
        "severity": "escalate",
        "patterns": [
            r"\b(being abused|domestic violence|partner hits me|afraid of my partner)\b",
            r"\b(sexual assault|raped|threatening to kill me)\b",
        ],
    },
]


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


def assess_crisis(user_prompt: str) -> Dict[str, Any]:
    """Detect crisis categories using deterministic pattern matching."""
    prompt_lower = (user_prompt or "").lower()
    matches: List[Dict[str, str]] = []

    for entry in CRISIS_PATTERNS:
        for pattern in entry["patterns"]:
            try:
                if re.search(pattern, prompt_lower, flags=re.IGNORECASE):
                    matches.append(
                        {
                            "category": entry["category"],
                            "severity": entry["severity"],
                        }
                    )
                    break
            except re.error:
                continue

    if not matches:
        return {
            "triggered": False,
            "categories": [],
            "playbook_steps": [],
        }

    categories = sorted({item["category"] for item in matches})
    config = _load_hard_constraints()
    playbook = config.get("escalation_playbook", {})
    steps: List[str] = []
    for category in categories:
        for step in playbook.get(category, []) or []:
            cleaned = str(step).strip()
            if cleaned and cleaned not in steps:
                steps.append(cleaned)

    return {
        "triggered": True,
        "categories": categories,
        "playbook_steps": steps,
    }
