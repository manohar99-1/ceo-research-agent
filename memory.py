"""
memory.py - Persistent memory system for the research agent
Stores facts, sources, and context across reasoning steps
"""

import json
from datetime import datetime
from typing import Any


class AgentMemory:
    """
    Maintains structured memory across all research steps.
    Acts like the agent's working notepad — accumulates facts,
    tracks sources, and logs every reasoning step.
    """

    def __init__(self, subject_name: str):
        self.subject_name = subject_name
        self.created_at = datetime.utcnow().isoformat()
        self.steps: list[dict] = []         # Ordered log of agent actions
        self.facts: dict[str, Any] = {}     # Key facts extracted
        self.raw_snippets: list[str] = []   # Raw text chunks from pages
        self.sources: list[str] = []        # All URLs visited
        self.search_queries: list[str] = [] # All queries issued

    # ── Logging ──────────────────────────────────────────────────────────────

    def log_step(self, action: str, detail: str = ""):
        step_num = len(self.steps) + 1
        entry = {
            "step": step_num,
            "action": action,
            "detail": detail,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.steps.append(entry)
        print(f"  📝 [Step {step_num}] {action}" + (f": {detail[:80]}" if detail else ""))

    def add_source(self, url: str):
        if url and url not in self.sources:
            self.sources.append(url)

    def add_query(self, query: str):
        if query not in self.search_queries:
            self.search_queries.append(query)

    def add_snippet(self, text: str, source_url: str = ""):
        if text:
            self.raw_snippets.append({
                "source": source_url,
                "text": text[:2000],
            })

    # ── Facts ────────────────────────────────────────────────────────────────

    def update_facts(self, new_facts: dict):
        """Merge new facts; never overwrite with empty/None."""
        for key, value in new_facts.items():
            if value and value not in ("", "Unknown", "N/A", None):
                # For lists, extend; for strings, overwrite only if blank
                if isinstance(value, list) and isinstance(self.facts.get(key), list):
                    existing = self.facts[key]
                    for item in value:
                        if item not in existing:
                            existing.append(item)
                else:
                    if not self.facts.get(key):
                        self.facts[key] = value

    def get_context_summary(self, max_chars: int = 6000) -> str:
        """Return a compact summary of everything gathered so far."""
        parts = [f"Subject: {self.subject_name}", f"Steps taken: {len(self.steps)}"]

        if self.facts:
            parts.append("\nFACTS SO FAR:")
            for k, v in self.facts.items():
                parts.append(f"  {k}: {v}")

        if self.raw_snippets:
            parts.append("\nRAW EVIDENCE:")
            total = 0
            for s in self.raw_snippets:
                snippet = f"[{s['source']}]\n{s['text']}"
                if total + len(snippet) > max_chars:
                    break
                parts.append(snippet)
                total += len(snippet)

        return "\n".join(parts)

    # ── Serialization ────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "subject_name": self.subject_name,
            "created_at": self.created_at,
            "memory_steps": len(self.steps),
            "steps_log": self.steps,
            "facts": self.facts,
            "sources": self.sources,
            "search_queries": self.search_queries,
        }

    def __repr__(self):
        return (
            f"AgentMemory(subject={self.subject_name!r}, "
            f"steps={len(self.steps)}, facts={len(self.facts)}, "
            f"sources={len(self.sources)})"
        )
