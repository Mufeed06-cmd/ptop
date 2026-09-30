import unittest
from schemas import Profile, LessonSection, Lesson, Question, Quiz, Answer, Result
from backend import generate_lesson, generate_quiz, submit_answers
from db import db
from engine import engine
from llm import llm_client


class TestLearnMate(unittest.TestCase):

    def test_schemas_instantiation(self):
        profile = Profile(name="Jane", minutes=20, skill_level="beginner")
        self.assertEqual(profile.name, "Jane")
        self.assertEqual(profile.minutes, 20)

        ans1 = Answer(question_id="q1", selected_answer="0, 1, 2, 3, 4")
        self.assertEqual(ans1.selected_answer, "0, 1, 2, 3, 4")

        # Test alias support
        ans2 = Answer.model_validate({"question_id": "q2", "selected_option": "3 times"})
        self.assertEqual(ans2.selected_answer, "3 times")

    def test_generate_lesson_sections_and_sum(self):
        for minutes in [6, 12, 15, 23, 30, 45]:
            profile = Profile(name="Alex", minutes=minutes)
            lesson = generate_lesson(profile)

            # Check 6 sections
            self.assertEqual(len(lesson.sections), 6)
            types = [s.type for s in lesson.sections]
            self.assertEqual(types, ["intro", "explain", "example", "practice", "quiz", "recap"])

            # Check minutes sum strictly to profile.minutes
            total_section_minutes = sum(s.minutes for s in lesson.sections)
            self.assertEqual(
                total_section_minutes,
                profile.minutes,
                f"Mismatch for profile minutes {minutes}: sum is {total_section_minutes}",
            )

            # Check example section animation
            example_sec = lesson.sections[2]
            self.assertEqual(example_sec.type, "example")
            self.assertEqual(
                example_sec.animation,
                {"component": "range_viz", "start": 0, "end": 5},
            )

    def test_generate_lesson_with_weak_concept(self):
        profile = Profile(name="Bob", minutes=15)
        lesson = generate_lesson(profile, weak_concept="range_bounds")
        self.assertEqual(lesson.weak_concept, "range_bounds")
        self.assertIn("range_bounds", lesson.sections[0].content)

    def test_generate_quiz(self):
        quiz = generate_quiz(concept_ids=["range_bounds", "loop_body"])
        self.assertEqual(len(quiz.questions), 5)

        concept_ids = set(q.concept_id for q in quiz.questions)
        self.assertTrue(concept_ids.issubset({"range_bounds", "loop_body"}))
        self.assertIn("range_bounds", concept_ids)
        self.assertIn("loop_body", concept_ids)

        for q in quiz.questions:
            self.assertTrue(len(q.options) >= 2)
            self.assertIn(q.correct_answer, q.options)

    def test_submit_answers_perfect(self):
        quiz = generate_quiz(["range_bounds", "loop_body"])
        answers = [Answer(question_id=q.id, selected_answer=q.correct_answer) for q in quiz.questions]
        result = submit_answers(answers)

        self.assertEqual(result.score, 5)
        self.assertEqual(result.total, 5)
        self.assertEqual(result.percentage, 100.0)
        self.assertTrue(result.passed)
        self.assertEqual(result.weak_concepts, [])

    def test_submit_answers_with_weak_concept_detection(self):
        quiz = generate_quiz(["range_bounds", "loop_body"])
        # Intentionally provide wrong answers for range_bounds questions
        answers = []
        for q in quiz.questions:
            if q.concept_id == "range_bounds":
                answers.append(Answer(question_id=q.id, selected_answer="WRONG_OPTION"))
            else:
                answers.append(Answer(question_id=q.id, selected_answer=q.correct_answer))

        result = submit_answers(answers)
        self.assertIn("range_bounds", result.weak_concepts)
        self.assertNotIn("loop_body", result.weak_concepts)

    def test_engine_integration(self):
        prof = engine.get_or_create_profile(name="Sam", minutes=18)
        lesson = engine.create_lesson(prof)
        self.assertEqual(sum(s.minutes for s in lesson.sections), 18)

        quiz = engine.create_quiz()
        self.assertEqual(len(quiz.questions), 5)

        # Submit answers via engine
        wrong_answers = [Answer(question_id="q1", selected_answer="WRONG")]
        result = engine.evaluate_quiz(wrong_answers, profile=prof)
        self.assertIn("range_bounds", prof.weak_concepts)

    def test_llm_client_mock_mode(self):
        self.assertFalse(llm_client.is_available)
        response = llm_client.generate("Explain loops")
        self.assertIn("[Mock Gemini Response]", response)


if __name__ == "__main__":
    unittest.main()
