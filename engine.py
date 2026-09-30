from __future__ import annotations

from typing import Optional
from schemas import Profile, Lesson, Quiz, Answer, Result
from backend import generate_lesson as _mock_generate_lesson
from backend import generate_quiz as _mock_generate_quiz
from backend import submit_answers as _mock_submit_answers
from db import db


class LearnMateEngine:
    """
    Adaptive learning engine that orchestrates lesson planning,
    quiz evaluation, and concept diagnosis.
    """

    def __init__(self):
        self.db = db

    def get_or_create_profile(
        self,
        name: str = "Learner",
        minutes: int = 15,
        skill_level: str = "beginner",
        user_id: str = "default_user",
    ) -> Profile:
        """Retrieves an existing profile or creates and stores a new one."""
        profile = self.db.get_profile(user_id)
        if not profile:
            profile = Profile(
                user_id=user_id,
                name=name,
                minutes=minutes,
                skill_level=skill_level,
                weak_concepts=[],
            )
            self.db.save_profile(profile)
        else:
            # Update attributes if modified
            profile.name = name
            profile.minutes = minutes
            profile.skill_level = skill_level
            self.db.save_profile(profile)
        return profile

    def create_lesson(self, profile: Profile, weak_concept: Optional[str] = None) -> Lesson:
        """
        Creates a lesson tailored to the learner's time limit and weak concepts,
        and saves it to the local store.
        """
        # If no explicit weak concept passed, prioritize one from profile history if present
        target_weak = weak_concept
        if not target_weak and profile.weak_concepts:
            target_weak = profile.weak_concepts[0]

        lesson = _mock_generate_lesson(profile=profile, weak_concept=target_weak)
        self.db.save_lesson(lesson)
        return lesson

    def create_quiz(self, concept_ids: Optional[list[str]] = None) -> Quiz:
        """Generates a quiz covering specific concept IDs."""
        concepts = concept_ids or ["range_bounds", "loop_body"]
        return _mock_generate_quiz(concept_ids=concepts)

    def evaluate_quiz(self, answers: list[Answer], profile: Optional[Profile] = None) -> Result:
        """
        Submits quiz answers, identifies weaknesses, updates the learner's profile,
        and records the result.
        """
        result = _mock_submit_answers(answers)
        self.db.save_result(result)

        if profile:
            # Update profile's weak concepts list (union of existing and new)
            updated_weak = sorted(list(set(profile.weak_concepts + result.weak_concepts)))
            profile.weak_concepts = updated_weak
            self.db.save_profile(profile)

        return result


# Global engine instance
engine = LearnMateEngine()
