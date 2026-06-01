import importlib
import importlib.util
import os
from typing import Any, Dict, List

import yaml

from skillware.core.base_skill import BaseSkill


def _load_local_module(module_name: str):
    try:
        package = __package__ or "skills.wellness.mental_coach"
        return importlib.import_module(f".{module_name}", package=package)
    except ImportError:
        module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
        spec = importlib.util.spec_from_file_location(
            f"mental_coach_{module_name}", module_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


_constraint_engine = _load_local_module("constraint_engine")
_crisis_gate = _load_local_module("crisis_gate")
_evaluator = _load_local_module("evaluator")
_kb_loader = _load_local_module("kb_loader")

evaluate_constraints = _constraint_engine.evaluate_constraints
required_disclaimers = _constraint_engine.required_disclaimers
assess_crisis = _crisis_gate.assess_crisis
run_scope_evaluator = _evaluator.run_scope_evaluator
build_citations = _kb_loader.build_citations
format_chunk_header = _kb_loader.format_chunk_header
load_corpus = _kb_loader.load_corpus
normalize_jurisdiction = _kb_loader.normalize_jurisdiction
normalize_session_mode = _kb_loader.normalize_session_mode
route_and_fetch = _kb_loader.route_and_fetch


class MentalCoachSkill(BaseSkill):
    """Grounded wellness coaching with embedded KB, crisis triage, and constraints."""

    @property
    def manifest(self) -> Dict[str, Any]:
        manifest_path = os.path.join(os.path.dirname(__file__), "manifest.yaml")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        return {"name": "wellness/mental_coach", "version": "0.1.0"}

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_input(params)
        if "error" in normalized:
            return normalized

        user_prompt = normalized["user_prompt"]
        session_mode = normalized["session_mode"]
        disclaimers = required_disclaimers(session_mode)

        crisis = assess_crisis(user_prompt)
        if crisis["triggered"]:
            return self._build_crisis_result(
                normalized=normalized,
                crisis=crisis,
                disclaimers=disclaimers,
            )

        constraints = evaluate_constraints(user_prompt)
        if constraints["action"] == "blocked":
            return self._build_blocked_result(
                normalized=normalized,
                constraints=constraints,
                disclaimers=disclaimers,
            )

        corpus = load_corpus()
        if not corpus:
            return {
                "policy_status": "BLOCKED",
                "scope": "blocked",
                "error": "Embedded knowledge base could not be loaded.",
                "retrieved_sections": [],
                "citations": [],
                "hard_constraints_applied": [item["id"] for item in constraints["hits"]],
                "disclaimers_required": disclaimers,
                "evaluator_feedback": self._disabled_evaluator_feedback(),
                "final_context_for_agent": (
                    "Do not provide coaching guidance. The knowledge base is unavailable."
                ),
                "privacy_metadata": {
                    "jurisdiction": normalized["user_jurisdiction"],
                    "session_mode": session_mode,
                },
            }

        chunks = route_and_fetch(
            user_prompt=user_prompt,
            corpus=corpus,
            jurisdiction=normalized["user_jurisdiction"],
            session_mode=session_mode,
            max_chunks=normalized["max_chunks"],
        )

        retrieved_sections: List[str] = []
        context_lines: List[str] = []
        for chunk in chunks:
            header = format_chunk_header(chunk)
            retrieved_sections.append(header)
            context_lines.append(f"--- {header} ---\n{chunk.get('content', '')}")

        context_text = "\n".join(context_lines)
        citations = build_citations(chunks)

        policy_status = "CAUTION"
        scope = session_mode
        if constraints["action"] == "caution":
            policy_status = "CAUTION"
        elif chunks:
            policy_status = "APPROVED"
        else:
            policy_status = "CAUTION"
            scope = "information"

        evaluator_feedback = self._disabled_evaluator_feedback()
        final_context = self._build_default_context(
            context_text=context_text,
            disclaimers=disclaimers,
            constraint_messages=constraints["messages"],
        )

        if normalized["run_evaluator"] and context_text:
            eval_result = run_scope_evaluator(
                user_prompt=user_prompt,
                context_text=context_text,
                disclaimers=disclaimers,
                model_name=normalized["evaluator_model"],
            )
            policy_status = eval_result.get("policy_status", policy_status)
            evaluator_feedback = eval_result.get(
                "evaluator_feedback", evaluator_feedback
            )
            final_context = eval_result.get("final_context_for_agent", final_context)
        elif not context_text:
            final_context = (
                "No specific knowledge-base sections matched this query. Provide "
                "only general supportive listening, required disclaimers, and "
                "encourage professional support if symptoms are severe or persistent."
            )

        return {
            "policy_status": policy_status,
            "scope": scope,
            "retrieved_sections": retrieved_sections,
            "citations": citations,
            "hard_constraints_applied": [item["id"] for item in constraints["hits"]],
            "disclaimers_required": disclaimers,
            "evaluator_feedback": evaluator_feedback,
            "final_context_for_agent": final_context,
            "privacy_metadata": {
                "jurisdiction": normalized["user_jurisdiction"],
                "session_mode": session_mode,
                "kb_chunks_retrieved": len(chunks),
            },
        }

    def _normalize_input(self, params: Dict[str, Any]) -> Dict[str, Any]:
        user_prompt = (params.get("user_prompt") or "").strip()
        if not user_prompt:
            return {"error": "user_prompt is required."}

        max_chunks = int(params.get("max_chunks", 8))
        max_chunks = max(1, min(max_chunks, 15))

        return {
            "user_prompt": user_prompt,
            "user_jurisdiction": normalize_jurisdiction(
                params.get("user_jurisdiction", "unknown")
            ),
            "session_mode": normalize_session_mode(params.get("session_mode", "coaching")),
            "run_evaluator": bool(params.get("run_evaluator", False)),
            "evaluator_model": params.get("evaluator_model", "gemini-2.5-flash-lite"),
            "max_chunks": max_chunks,
        }

    def _build_crisis_result(
        self,
        normalized: Dict[str, Any],
        crisis: Dict[str, Any],
        disclaimers: List[str],
    ) -> Dict[str, Any]:
        steps = crisis.get("playbook_steps") or []
        playbook_text = "\n".join(f"- {step}" for step in steps)
        return {
            "policy_status": "ESCALATE",
            "scope": "crisis_referral",
            "retrieved_sections": [],
            "citations": [],
            "hard_constraints_applied": ["crisis_escalation"],
            "crisis_categories": crisis.get("categories", []),
            "disclaimers_required": disclaimers,
            "evaluator_feedback": self._disabled_evaluator_feedback(
                "Crisis triage triggered. Do not continue standard coaching."
            ),
            "final_context_for_agent": (
                "Crisis signals were detected. Stop coaching. Respond with empathy, "
                "prioritize immediate safety, and share the escalation steps below. "
                "Do not minimize the user's experience or attempt diagnosis.\n\n"
                f"Escalation steps:\n{playbook_text}"
            ),
            "privacy_metadata": {
                "jurisdiction": normalized["user_jurisdiction"],
                "session_mode": normalized["session_mode"],
            },
        }

    def _build_blocked_result(
        self,
        normalized: Dict[str, Any],
        constraints: Dict[str, Any],
        disclaimers: List[str],
    ) -> Dict[str, Any]:
        messages = constraints.get("messages") or [
            "This request is outside supported coaching scope."
        ]
        guidance = "\n".join(f"- {message}" for message in messages)
        return {
            "policy_status": "BLOCKED",
            "scope": "blocked",
            "retrieved_sections": [],
            "citations": [],
            "hard_constraints_applied": [item["id"] for item in constraints["hits"]],
            "disclaimers_required": disclaimers,
            "evaluator_feedback": self._disabled_evaluator_feedback(
                "Request blocked by hard constraints."
            ),
            "final_context_for_agent": (
                "The user's request is outside supported coaching scope. Decline the "
                "clinical request clearly and offer non-clinical alternatives where "
                "appropriate.\n\n"
                f"Constraint guidance:\n{guidance}"
            ),
            "privacy_metadata": {
                "jurisdiction": normalized["user_jurisdiction"],
                "session_mode": normalized["session_mode"],
            },
        }

    @staticmethod
    def _disabled_evaluator_feedback(reason: str = None) -> Dict[str, str]:
        holes_found = reason or "Evaluator disabled. Review retrieved guidance manually."
        return {
            "grade": "N/A",
            "holes_found": holes_found,
            "suggestion": "Follow retrieved chunks and required disclaimers exactly.",
        }

    @staticmethod
    def _build_default_context(
        context_text: str,
        disclaimers: List[str],
        constraint_messages: List[str],
    ) -> str:
        disclaimer_block = "\n".join(f"- {line}" for line in disclaimers)
        constraint_block = ""
        if constraint_messages:
            constraint_block = "Constraint reminders:\n" + "\n".join(
                f"- {message}" for message in constraint_messages
            )
        return (
            "Provide supportive coaching using ONLY the retrieved guidance below. "
            "Cite source sections in plain language. Do not diagnose, prescribe, "
            "or interpret clinical records.\n\n"
            f"Required disclaimers:\n{disclaimer_block}\n\n"
            f"{constraint_block}\n\n"
            f"Retrieved guidance:\n{context_text}"
        ).strip()
