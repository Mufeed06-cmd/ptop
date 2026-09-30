import os
import unittest
from unittest.mock import patch, MagicMock
from schemas import Profile, LessonSection, Lesson, Question, Quiz, Answer, Result
import db
from engine import engine, LearningEngine
from llm import llm_service, get_fallback_lesson, get_fallback_quiz
from backend import generate_lesson, generate_quiz, submit_answers


class TestLearnMateRealLogic(unittest.TestCase):

    def setUp(self):
        # Reset database before each test
        db.reset_db()

    def test_db_schema_and_defaults(self):
        """Verify SQLite tables: sessions, questions, attempts, mastery with default 0.5."""
        # Check default mastery score of 0.5
        score = db.get_mastery("range_bounds")
        self.assertEqual(score, 0.5)

        # Update mastery
        db.update_mastery("range_bounds", 0.65)
        self.assertEqual(db.get_mastery("range_bounds"), 0.65)

        # Check all mastery
        all_m = db.get_all_mastery()
        self.assertIn("range_bounds", all_m)

        # Check session saving
        db.save_session("sess_1", "user_1", "Python Loops")
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM sessions WHERE id = 'sess_1'")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["user_id"], "user_1")

    def test_engine_score_against_correct_index(self):
        """Verify scoring answers against correct_index and recording attempts."""
        q1 = Question(
            id="q1",
            concept_id="range_bounds",
            question="What is range(0, 2)?",
            options=["0, 1", "0, 1, 2", "1, 2", "none"],
            correct_index=0,
            explanation="Range stops at stop-1.",
        )
        questions_dict = {"q1": q1}

        # Correct answer using selected_index=0
        ans_correct = [Answer(question_id="q1", selected_index=0)]
        res_correct = engine.score_and_update(ans_correct, questions_dict, session_id="s1")
        self.assertEqual(res_correct.score, 1)
        self.assertTrue(res_correct.details[0]["is_correct"])

        # Check attempt in DB
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM attempts WHERE question_id = 'q1'")
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["outcome"], 1.0)
            self.assertEqual(row["selected_index"], 0)

        # Incorrect answer using selected_index=1
        ans_wrong = [Answer(question_id="q1", selected_index=1)]
        res_wrong = engine.score_and_update(ans_wrong, questions_dict, session_id="s2")
        self.assertEqual(res_wrong.score, 0)
        self.assertFalse(res_wrong.details[0]["is_correct"])

    def test_engine_mastery_formula(self):
        """
        Verify formula: mastery += 0.3 * (outcome - mastery)
        Initial default mastery: 0.5
        If outcome = 1.0 -> 0.5 + 0.3 * (1.0 - 0.5) = 0.5 + 0.15 = 0.65
        If outcome = 0.0 -> 0.65 + 0.3 * (0.0 - 0.65) = 0.65 - 0.195 = 0.455
        """
        calc = LearningEngine.calculate_mastery_update
        self.assertAlmostEqual(calc(0.5, 1.0), 0.65, places=3)
        self.assertAlmostEqual(calc(0.65, 0.0), 0.455, places=3)
        self.assertAlmostEqual(calc(0.5, 0.0), 0.35, places=3)

    def test_weak_concept_lowest_below_0_6(self):
        """
        Verify weak_concept = lowest mastery concept below 0.6.
        If all >= 0.6, weak_concept = None.
        """
        # Both below 0.6: range_bounds=0.45, loop_body=0.35 -> weak_concept = loop_body
        masteries = {"range_bounds": 0.45, "loop_body": 0.35}
        self.assertEqual(LearningEngine.determine_weak_concept(masteries), "loop_body")

        # One below 0.6: range_bounds=0.65, loop_body=0.55 -> weak_concept = loop_body
        masteries = {"range_bounds": 0.65, "loop_body": 0.55}
        self.assertEqual(LearningEngine.determine_weak_concept(masteries), "loop_body")

        # Both above or equal to 0.6 -> None
        masteries = {"range_bounds": 0.65, "loop_body": 0.70}
        self.assertIsNone(LearningEngine.determine_weak_concept(masteries))

    def test_next_focus_one_line_string(self):
        """Verify next_focus is a one-line string explaining what the next lesson will focus on."""
        focus_weak = LearningEngine.generate_next_focus("range_bounds")
        self.assertIn("range_bounds", focus_weak)
        self.assertEqual(len(focus_weak.splitlines()), 1)

        focus_none = LearningEngine.generate_next_focus(None)
        self.assertIsInstance(focus_none, str)
        self.assertEqual(len(focus_none.splitlines()), 1)

    def test_fallback_lesson_and_quiz(self):
        """Verify fallback lesson adheres to sections, minutes sum, and range_viz animation."""
        p = Profile(name="Tester", minutes=20, language="Spanish")
        lesson = get_fallback_lesson(p, weak_concept="range_bounds")
        self.assertEqual(len(lesson.sections), 6)
        self.assertEqual(sum(s.minutes for s in lesson.sections), 20)
        self.assertEqual(lesson.sections[2].animation, {"component": "range_viz", "start": 0, "end": 5})

        quiz = get_fallback_quiz(["range_bounds", "loop_body"])
        self.assertEqual(len(quiz.questions), 5)
        for q in quiz.questions:
            self.assertIn(q.concept_id, ["range_bounds", "loop_body"])
            self.assertTrue(0 <= q.correct_index < len(q.options))

    def test_llm_service_prompt_requirements(self):
        """
        Verify lesson prompt includes:
        - "Explain in {language}. Keep code and technical terms in English."
        - "The student struggled with {weak_concept}. Use a step-by-step trace explanation and address the common mistake."
        """
        p = Profile(name="Maria", minutes=15, language="French")

        # Spy on _call_gemini_raw
        with patch.object(llm_service, "_call_gemini_raw") as mock_call:
            mock_call.side_effect = RuntimeError("Mock network failure")
            lesson = llm_service.generate_lesson_llm(p, weak_concept="loop_body")

            # Check prompt passed into first call
            called_prompt = mock_call.call_args_list[0][0][0]
            self.assertIn("Explain in French. Keep code and technical terms in English.", called_prompt)
            self.assertIn("The student struggled with loop_body. Use a step-by-step trace explanation and address the common mistake.", called_prompt)

            # Even on failure, fallback lesson was returned cleanly
            self.assertIsNotNone(lesson)
            self.assertEqual(len(lesson.sections), 6)
            self.assertEqual(sum(s.minutes for s in lesson.sections), 15)

    def test_llm_service_retry_once_on_invalid_json(self):
        """Verify that if Gemini output is invalid, it retries once with the error message."""
        p = Profile(name="David", minutes=12, language="English")

        with patch.object(llm_service, "_call_gemini_raw") as mock_call:
            # First response is invalid JSON, second response is valid JSON
            valid_json = get_fallback_lesson(p).model_dump_json()
            mock_call.side_effect = ["INVALID_NOT_JSON", valid_json]

            lesson = llm_service.generate_lesson_llm(p)

            # Check that two calls were made (original + 1 retry)
            self.assertEqual(mock_call.call_count, 2)
            retry_prompt = mock_call.call_args_list[1][0][0]
            self.assertIn("failed validation with error", retry_prompt)
            self.assertIsNotNone(lesson)

    def test_backend_end_to_end(self):
        """End-to-end test of backend.py: generate_lesson, generate_quiz, submit_answers."""
        p = Profile(name="Sarah", minutes=18)
        lesson = generate_lesson(p)
        self.assertEqual(sum(s.minutes for s in lesson.sections), 18)
        self.assertEqual(lesson.sections[2].animation, {"component": "range_viz", "start": 0, "end": 5})

        quiz = generate_quiz(["range_bounds", "loop_body"])
        self.assertEqual(len(quiz.questions), 5)

        # Submit all correct answers
        answers = [
            Answer(question_id=q.id, selected_index=q.correct_index)
            for q in quiz.questions
        ]
        result = submit_answers(answers)
        self.assertEqual(result.score, 5)
        self.assertEqual(result.total, 5)
        self.assertEqual(result.percentage, 100.0)
        self.assertIsNotNone(result.next_focus)

        # 3 range_bounds questions: 0.5 -> 0.65 -> 0.755 -> 0.8285
        self.assertAlmostEqual(result.mastery_scores["range_bounds"], 0.8285, places=3)
        # 2 loop_body questions: 0.5 -> 0.65 -> 0.755
        self.assertAlmostEqual(result.mastery_scores["loop_body"], 0.755, places=3)


if __name__ == "__main__":
    unittest.main()
