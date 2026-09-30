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
    language: str = "English"
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
    language: str = "English"


class Question(BaseModel):
    """Single quiz question item."""
    model_config = ConfigDict(extra="ignore")

    id: str
    concept_id: str  # e.g., "range_bounds", "loop_body"
    question: str
    options: list[str]
    correct_index: int
    correct_answer: Optional[str] = None
    explanation: str

    @model_validator(mode="after")
    def sync_answers(self) -> Question:
        if self.options and 0 <= self.correct_index < len(self.options):
            if not self.correct_answer:
                self.correct_answer = self.options[self.correct_index]
        elif self.correct_answer and self.options and self.correct_answer in self.options:
            self.correct_index = self.options.index(self.correct_answer)
        return self


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
    selected_index: int = -1
    selected_answer: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_alias_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "selected_index" not in data:
                if "index" in data:
                    data["selected_index"] = data["index"]
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
    weak_concept: Optional[str] = None
    next_focus: Optional[str] = None
    mastery_scores: dict[str, float] = Field(default_factory=dict)
    details: list[dict[str, Any]] = Field(default_factory=list)
