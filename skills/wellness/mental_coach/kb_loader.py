"""Load and route embedded mental coach knowledge-base chunks."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import yaml

_KB_DIR = os.path.join(os.path.dirname(__file__), "kb")
_CORPUS_CACHE: Optional[List[Dict[str, Any]]] = None
_CONSTRAINTS_CACHE: Optional[Dict[str, Any]] = None

VALID_JURISDICTIONS = frozenset({"US", "EU", "UK", "GLOBAL", "UNKNOWN"})
VALID_SESSION_MODES = frozenset({"coaching", "information", "crisis_check"})


def load_corpus() -> List[Dict[str, Any]]:
    global _CORPUS_CACHE
    if _CORPUS_CACHE is not None:
        return _CORPUS_CACHE

    corpus_path = os.path.join(_KB_DIR, "corpus.json")
    try:
        with open(corpus_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        _CORPUS_CACHE = data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        _CORPUS_CACHE = []
    return _CORPUS_CACHE


def load_hard_constraints() -> Dict[str, Any]:
    global _CONSTRAINTS_CACHE
    if _CONSTRAINTS_CACHE is not None:
        return _CONSTRAINTS_CACHE

    constraints_path = os.path.join(_KB_DIR, "hard_constraints.yaml")
    try:
        with open(constraints_path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        _CONSTRAINTS_CACHE = data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        _CONSTRAINTS_CACHE = {}
    return _CONSTRAINTS_CACHE


def normalize_jurisdiction(value: str) -> str:
    cleaned = (value or "unknown").strip().upper()
    if cleaned in VALID_JURISDICTIONS:
        return cleaned
    return "UNKNOWN"


def normalize_session_mode(value: str) -> str:
    cleaned = (value or "coaching").strip().lower()
    if cleaned in VALID_SESSION_MODES:
        return cleaned
    return "coaching"


def _jurisdiction_matches(chunk: Dict[str, Any], jurisdiction: str) -> bool:
    chunk_jurisdiction = (chunk.get("jurisdiction") or "GLOBAL").upper()
    if jurisdiction in {"UNKNOWN", "GLOBAL"}:
        return True
    if chunk_jurisdiction == "GLOBAL":
        return True
    return chunk_jurisdiction == jurisdiction


def _session_doc_types(session_mode: str) -> Optional[frozenset]:
    if session_mode == "crisis_check":
        return frozenset({"crisis_resource", "policy", "regulation"})
    if session_mode == "information":
        return frozenset({"regulation", "guideline", "policy"})
    return None


def route_and_fetch(
    user_prompt: str,
    corpus: List[Dict[str, Any]],
    jurisdiction: str = "UNKNOWN",
    session_mode: str = "coaching",
    max_chunks: int = 8,
) -> List[Dict[str, Any]]:
    """Return top matching KB chunks using weighted keyword routing."""
    if not corpus or not user_prompt.strip():
        return []

    prompt_lower = user_prompt.lower()
    prompt_words = [
        word
        for word in re.sub(r"[^\w\s-]", " ", prompt_lower).split()
        if len(word) > 3
    ]
    allowed_doc_types = _session_doc_types(session_mode)
    scored: List[tuple] = []

    for chunk in corpus:
        if not _jurisdiction_matches(chunk, jurisdiction):
            continue

        doc_type = (chunk.get("doc_type") or "").lower()
        if allowed_doc_types and doc_type not in allowed_doc_types:
            continue

        score = 0.0
        section = (chunk.get("section") or "").lower()
        source_doc = (chunk.get("source_doc") or "").lower()
        keywords = [str(keyword).lower() for keyword in chunk.get("keywords", [])]
        constraint_tags = [
            str(tag).lower() for tag in chunk.get("constraint_tags", [])
        ]

        for keyword in keywords:
            if keyword in prompt_lower:
                score += 20

        for word in prompt_words:
            if word in section or word in source_doc:
                score += 8
            for keyword in keywords:
                if word in keyword:
                    score += 5 * (len(word) / max(len(keyword), 1))

        if session_mode == "coaching" and "coaching" in constraint_tags:
            score += 6
        if session_mode == "crisis_check" and "crisis" in constraint_tags:
            score += 25
        if "stress" in prompt_lower and "stress" in keywords:
            score += 10
        if "anxiety" in prompt_lower and "anxiety" in keywords:
            score += 10
        if "sleep" in prompt_lower and "sleep" in keywords:
            score += 10

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)

    unique: List[Dict[str, Any]] = []
    seen_ids = set()
    for _, chunk in scored:
        chunk_id = chunk.get("chunk_id")
        if chunk_id in seen_ids:
            continue
        unique.append(chunk)
        seen_ids.add(chunk_id)
        if len(unique) >= max_chunks:
            break

    return unique


def format_chunk_header(chunk: Dict[str, Any]) -> str:
    source = chunk.get("source_doc", "Unknown source")
    section = chunk.get("section", "General")
    chunk_id = chunk.get("chunk_id", "unknown")
    return f"{source} | {section} [{chunk_id}]"


def build_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    citations = []
    for chunk in chunks:
        citations.append(
            {
                "chunk_id": str(chunk.get("chunk_id", "")),
                "source_doc": str(chunk.get("source_doc", "")),
                "section": str(chunk.get("section", "")),
                "jurisdiction": str(chunk.get("jurisdiction", "")),
            }
        )
    return citations
