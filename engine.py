from __future__ import annotations

from typing import Optional
from schemas import Profile, Question, Answer, Result
import db


class LearningEngine:
    """
    Adaptive mastery and pedagogical engine.
    - Evaluates quiz answers against question.correct_index
    - Updates mastery score per concept: mastery += 0.3 * (outcome - mastery)
    - Detects weak_concept = lowest mastery concept below 0.6
    - Generates next_focus = a one-line string explaining what the next lesson will focus on
    """

    @staticmethod
    def calculate_mastery_update(current_mastery: float, outcome: float) -> float:
        """
        Updates concept mastery via:
        mastery += 0.3 * (outcome - mastery)
        """
        new_mastery = current_mastery + 0.3 * (outcome - current_mastery)
        return round(max(0.0, min(1.0, new_mastery)), 4)

    @staticmethod
    def determine_weak_concept(mastery_dict: dict[str, float]) -> Optional[str]:
        """
        weak_concept = lowest mastery concept below 0.6.
        Returns None if all concepts are >= 0.6.
        """
        below_threshold = {cid: score for cid, score in mastery_dict.items() if score < 0.6}
        if not below_threshold:
            return None
        return min(below_threshold.keys(), key=lambda cid: below_threshold[cid])

    @staticmethod
    def generate_next_focus(weak_concept: Optional[str]) -> str:
        """
        next_focus = a one-line string explaining what the next lesson will focus on.
        """
        if weak_concept:
            return f"The next lesson will focus on mastering '{weak_concept}' using step-by-step trace explanations."
        return "The next lesson will focus on advanced loop structures, nested iterations, and optimization patterns."

    def score_and_update(
        self,
        answers: list[Answer],
        questions_dict: dict[str, Question],
        session_id: Optional[str] = None,
    ) -> Result:
        """
        Scores answers against question.correct_index,
        updates concept mastery in SQLite, determines weak_concept and next_focus.
        """
        total = len(questions_dict)
        score = 0
        details: list[dict] = []

        # Map answer by question_id
        answer_map = {ans.question_id: ans for ans in answers}

        for qid, q in questions_dict.items():
            ans = answer_map.get(qid)
            selected_idx = -1
            selected_text = ""

            if ans is not None:
                selected_idx = ans.selected_index
                selected_text = ans.selected_answer or ""
                # If selected_index was not set but selected_answer was, resolve index
                if selected_idx < 0 and selected_text and q.options:
                    try:
                        selected_idx = q.options.index(selected_text)
                    except ValueError:
                        selected_idx = -1
                elif selected_idx >= 0 and q.options and selected_idx < len(q.options):
                    if not selected_text:
                        selected_text = q.options[selected_idx]

            # Score against correct_index
            is_correct = (selected_idx == q.correct_index)
            outcome = 1.0 if is_correct else 0.0

            if is_correct:
                score += 1

            # Record attempt in SQLite
            db.record_attempt(
                session_id=session_id,
                question_id=q.id,
                selected_index=selected_idx,
                outcome=outcome,
            )

            # Update concept mastery in SQLite: mastery += 0.3 * (outcome - mastery)
            current_mastery = db.get_mastery(q.concept_id)
            updated_mastery = self.calculate_mastery_update(current_mastery, outcome)
            db.update_mastery(q.concept_id, updated_mastery)

            correct_text = q.options[q.correct_index] if 0 <= q.correct_index < len(q.options) else q.correct_answer

            details.append({
                "question_id": q.id,
                "concept_id": q.concept_id,
                "question": q.question,
                "selected_index": selected_idx,
                "selected_answer": selected_text,
                "correct_index": q.correct_index,
                "correct_answer": correct_text,
                "is_correct": is_correct,
                "explanation": q.explanation,
            })

        all_masteries = db.get_all_mastery()
        weak_concept = self.determine_weak_concept(all_masteries)
        weak_concepts = [cid for cid, m in all_masteries.items() if m < 0.6]
        next_focus = self.generate_next_focus(weak_concept)

        percentage = round((score / total) * 100, 1) if total > 0 else 0.0
        passed = percentage >= 60.0

        if score == total:
            feedback = "Flawless score! Full mastery demonstrated across evaluated concepts."
        elif passed:
            feedback = "Great performance! Review your identified focus area to consolidate mastery."
        else:
            feedback = "Solid practice attempt! Further review on weaker concepts will build confidence."

        return Result(
            score=score,
            total=total,
            percentage=percentage,
            passed=passed,
            feedback=feedback,
            weak_concepts=weak_concepts,
            weak_concept=weak_concept,
            next_focus=next_focus,
            mastery_scores=all_masteries,
            details=details,
        )


engine = LearningEngine()
