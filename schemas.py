from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Profile(BaseModel):
    """User learner profile."""
    model_config = ConfigDict(extra="ignore")

    user_id: str = "user_default"
    name: str = "Learner"
    skill_level: str = "beginner"
    minutes: int = 15
    weak_concepts: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)


class LessonSection(BaseModel):
    """Individual section of a generated lesson."""
    model_config = ConfigDict(extra="ignore")

    id: str
    type: str  # "intro" | "explain" | "example" | "practice" | "quiz" | "recap"
    title: str
    content: str
    minutes: int
    animation: Optional[dict[str, Any]] = None
    code: Optional[str] = None


class Lesson(BaseModel):
    """Full lesson containing structured sections."""
    model_config = ConfigDict(extra="ignore")

    id: str
    topic: str
    total_minutes: int
    sections: list[LessonSection]
    weak_concept: Optional[str] = None


class Question(BaseModel):
    """Single quiz question item."""
    model_config = ConfigDict(extra="ignore")

    id: str
    concept_id: str  # e.g., "range_bounds", "loop_body"
    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class Quiz(BaseModel):
    """Quiz set covering specific concepts."""
    model_config = ConfigDict(extra="ignore")

    id: str
    topic: str
    concept_ids: list[str]
    questions: list[Question]


class Answer(BaseModel):
    """Submitted answer for a quiz question."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    question_id: str
    selected_answer: str

    @model_validator(mode="before")
    @classmethod
    def populate_alias_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Allow 'selected_option' or 'answer' as fallback aliases
            if "selected_answer" not in data:
                if "selected_option" in data:
                    data["selected_answer"] = data["selected_option"]
                elif "answer" in data:
                    data["selected_answer"] = data["answer"]
        return data


class Result(BaseModel):
    """Evaluated result of submitted quiz answers."""
    model_config = ConfigDict(extra="ignore")

    score: int
    total: int
    percentage: float
    passed: bool
    feedback: str
    weak_concepts: list[str] = Field(default_factory=list)
    details: list[dict[str, Any]] = Field(default_factory=list)
