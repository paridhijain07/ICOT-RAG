from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VALID_FACETS = {
    "behaviour",
    "technique",
    "vulnerability",
    "exploit",
    "mitigation",
}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}


@dataclass
class EvalQuestion:
    id: str
    question: str
    category: str
    required_facets: list[str]
    expected_sources: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    gold_notes: str = ""
    reference_hints: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []

        if not self.id:
            errors.append("missing id")
        if not self.question.strip():
            errors.append(f"{self.id}: empty question")
        if self.difficulty not in VALID_DIFFICULTIES:
            errors.append(f"{self.id}: bad difficulty {self.difficulty}")

        bad_facets = [
            f for f in self.required_facets if f not in VALID_FACETS
        ]
        if bad_facets:
            errors.append(f"{self.id}: invalid facets {bad_facets}")

        return errors

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvalQuestion":
        return cls(
            id=data["id"],
            question=data["question"],
            category=data.get("category", "general"),
            required_facets=list(data.get("required_facets", [])),
            expected_sources=list(data.get("expected_sources", [])),
            difficulty=data.get("difficulty", "medium"),
            gold_notes=data.get("gold_notes", ""),
            reference_hints=list(data.get("reference_hints", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "category": self.category,
            "required_facets": self.required_facets,
            "expected_sources": self.expected_sources,
            "difficulty": self.difficulty,
            "gold_notes": self.gold_notes,
            "reference_hints": self.reference_hints,
        }


def load_eval_dataset(path: str | Path) -> list[EvalQuestion]:
    path = Path(path)

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict) and "questions" in raw:
        items = raw["questions"]
    else:
        items = raw

    questions = [EvalQuestion.from_dict(item) for item in items]

    errors = []
    for q in questions:
        errors.extend(q.validate())

    if errors:
        raise ValueError(
            "Eval dataset validation failed:\n- " + "\n- ".join(errors)
        )

    return questions


def summarize_dataset(questions: list[EvalQuestion]) -> dict[str, Any]:
    return {
        "count": len(questions),
        "by_category": dict(Counter(q.category for q in questions)),
        "by_difficulty": dict(Counter(q.difficulty for q in questions)),
        "facet_demand": dict(
            Counter(
                facet
                for q in questions
                for facet in q.required_facets
            )
        ),
    }
