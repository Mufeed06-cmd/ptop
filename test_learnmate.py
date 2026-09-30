import json
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

    def test_mastery_keyed_by_topic_and_concept(self):
        """Requirement 4: Key mastery by (topic, concept_id) in db.py so topics don't mix."""
        # Update concept in Topic A
        db.update_mastery("join_logic", 0.85, topic="SQL joins")
        # Update same concept name in Topic B
        db.update_mastery("join_logic", 0.35, topic="Photosynthesis")

        # Distinct scores retrieved per topic
        self.assertEqual(db.get_mastery("join_logic", topic="SQL joins"), 0.85)
        self.assertEqual(db.get_mastery("join_logic", topic="Photosynthesis"), 0.35)

        # Topic filtering in get_all_mastery
        all_sql = db.get_all_mastery(topic="SQL joins")
        self.assertIn("join_logic", all_sql)
        self.assertEqual(all_sql["join_logic"], 0.85)

        all_photo = db.get_all_mastery(topic="Photosynthesis")
        self.assertIn("join_logic", all_photo)
        self.assertEqual(all_photo["join_logic"], 0.35)

    def test_generate_concepts_and_caching(self):
        """Requirement 2: generate_concepts(topic, level, goal) returns 3 items {concept_id, name, common_mistake} and caches."""
        from llm import generate_concepts

        # Test fallback concepts for Python loops
        concepts_py = generate_concepts("Python loops")
        self.assertEqual(len(concepts_py), 3)
        for c in concepts_py:
            self.assertIn("concept_id", c)
            self.assertIn("name", c)
            self.assertIn("common_mistake", c)
            # Must be snake_case
            self.assertTrue(c["concept_id"].islower() or "_" in c["concept_id"])

        # Test live generation with mock for arbitrary topic
        mock_concepts_json = json.dumps([
            {"concept_id": "table_joining", "name": "Table Joining", "common_mistake": "Unintentional cartesian join"},
            {"concept_id": "null_handling", "name": "NULL Handling", "common_mistake": "Believing inner join preserves NULLs"},
            {"concept_id": "where_vs_on", "name": "WHERE vs ON", "common_mistake": "Filtering in WHERE instead of ON"},
        ])

        with patch.object(llm_service, "_call_gemini_raw") as mock_call:
            mock_call.return_value = mock_concepts_json
            concepts_sql = generate_concepts("SQL joins", level="intermediate")
            self.assertEqual(len(concepts_sql), 3)
            self.assertEqual(concepts_sql[0]["concept_id"], "table_joining")
            self.assertEqual(mock_call.call_count, 1)

            # Calling again should read from cache and NOT invoke _call_gemini_raw
            cached_sql = generate_concepts("SQL joins", level="intermediate")
            self.assertEqual(len(cached_sql), 3)
            self.assertEqual(mock_call.call_count, 1)  # No extra call!

    def test_quiz_reject_and_retry_if_rule_broken(self):
        """Requirement 3: Exactly 5 quiz questions, 4 options each, concept_id from list. Reject & retry on violation."""
        allowed_concepts = ["c1", "c2", "c3"]
        invalid_quiz_json = json.dumps({
            "id": "q_invalid",
            "topic": "Test Topic",
            "concept_ids": allowed_concepts,
            "questions": [
                # Only 1 question instead of 5
                {"id": "q1", "concept_id": "c1", "question": "Q1?", "options": ["A", "B"], "correct_index": 0, "explanation": "Exp"}
            ]
        })

        valid_quiz_json = json.dumps({
            "id": "q_valid",
            "topic": "Test Topic",
            "concept_ids": allowed_concepts,
            "questions": [
                {"id": f"q{i}", "concept_id": allowed_concepts[i % 3], "question": f"Q{i}?", "options": ["A", "B", "C", "D"], "correct_index": 0, "explanation": f"Exp {i}"}
                for i in range(1, 6)
            ]
        })

        with patch.object(llm_service, "_call_gemini_raw") as mock_call:
            mock_call.side_effect = [invalid_quiz_json, valid_quiz_json]
            quiz = llm_service.generate_quiz_llm(allowed_concepts, topic="Test Topic")
            # Should have rejected first attempt and retried once
            self.assertEqual(mock_call.call_count, 2)
            self.assertEqual(len(quiz.questions), 5)
            for q in quiz.questions:
                self.assertIn(q.concept_id, allowed_concepts)
                self.assertEqual(len(q.options), 4)

    def test_failure_handling_and_offline_python_loops(self):
        """Requirement 7: If no API key or Gemini fails for new topic, raise LiveAINeededError. Python loops keeps working offline."""
        from llm import LiveAINeededError

        # New topic fails when live AI fails (Gemini and Groq fallback both fail)
        with patch.object(llm_service, "_call_gemini_raw") as mock_call, \
             patch.object(llm_service, "_call_groq_raw") as mock_groq:
            mock_call.side_effect = RuntimeError("Network error")
            mock_groq.side_effect = RuntimeError("Groq offline")
            with self.assertRaises(LiveAINeededError) as ctx:
                generate_lesson(Profile(name="Student", topic="Photosynthesis", minutes=15))
            self.assertIn("Live AI is needed for this topic. Try Python loops.", str(ctx.exception))

        # Python loops keeps working offline with fallback
        with patch.object(llm_service, "_call_gemini_raw") as mock_call, \
             patch.object(llm_service, "_call_groq_raw") as mock_groq:
            mock_call.side_effect = RuntimeError("Offline")
            mock_groq.side_effect = RuntimeError("Groq offline")
            lesson = generate_lesson(Profile(name="Student", topic="Python loops", minutes=15))
            self.assertIsNotNone(lesson)
            self.assertEqual(len(lesson.sections), 6)
            self.assertEqual(lesson.source, "Fallback")

    def test_badge_and_lesson_caching(self):
        """Requirement 8: Show badge Live AI, Cached, or Fallback. Cache by topic+level+language+minutes+weak_concept in cache/."""
        # 1. Fallback badge
        with patch.object(llm_service, "_call_gemini_raw") as mock_call, \
             patch.object(llm_service, "_call_groq_raw") as mock_groq:
            mock_call.side_effect = RuntimeError("Simulate offline")
            mock_groq.side_effect = RuntimeError("Groq offline")
            fallback_lesson = llm_service.generate_lesson_llm(Profile(topic="Python loops", minutes=15))
            self.assertEqual(fallback_lesson.source, "Fallback")

        # 2. Live AI badge & caching
        valid_lesson = get_fallback_lesson(Profile(topic="Python loops", minutes=15))
        valid_lesson_json = valid_lesson.model_dump_json()

        with patch.object(llm_service, "_call_gemini_raw") as mock_call:
            mock_call.return_value = valid_lesson_json
            p = Profile(name="CacheTester", topic="Python loops", minutes=16, language="English", skill_level="beginner")
            lesson_live = llm_service.generate_lesson_llm(p)
            self.assertEqual(lesson_live.source, "Live AI")
            self.assertEqual(mock_call.call_count, 1)

            # 3. Next call with same topic+level+language+minutes+weak_concept hits cache
            lesson_cached = llm_service.generate_lesson_llm(p)
            self.assertEqual(lesson_cached.source, "Cached")
            self.assertEqual(mock_call.call_count, 1)  # No extra LLM call!

    def test_generic_step_viz_animation(self):
        """Requirement 6: step_viz component in animations.py with stepper, Previous/Next, and progress bar."""
        from animations import render_step_visualizer_html, render_animation

        steps = [
            {"title": "Step 1: Light Absorption", "detail": "Chlorophyll absorbs photons."},
            {"title": "Step 2: Electron Transport", "detail": "Electrons pass through thylakoid membrane."},
            {"title": "Step 3: ATP Synthesis", "detail": "Proton gradient drives ATP synthase."},
        ]
        html = render_step_visualizer_html(steps)
        self.assertIn("Step 1: Light Absorption", html)
        self.assertIn("Previous", html)
        self.assertIn("Next", html)
        self.assertIn("progress-fill", html)

        # Invalid or missing steps should not crash
        try:
            render_animation({"component": "step_viz", "steps": []})
            render_animation({"component": "step_viz"})
            render_animation({"component": "step_viz", "steps": "invalid"})
            render_animation(None)
        except Exception as e:
            self.fail(f"render_animation crashed on invalid input: {e}")

    def test_get_gemini_api_key_stripping_and_secrets(self):
        """Step 3: Test that API key strips quotes, whitespace, and works with env and secrets."""
        from llm import get_gemini_api_key
        import os

        # Test placeholder ignored
        with patch.dict(os.environ, {"GEMINI_API_KEY": "paste_your_key_here"}):
            self.assertIsNone(get_gemini_api_key())

        # Test whitespace and double quotes stripped
        with patch.dict(os.environ, {"GEMINI_API_KEY": '  "AIzaSyFakeKeyWithQuotes"  '}):
            key = get_gemini_api_key()
            self.assertEqual(key, "AIzaSyFakeKeyWithQuotes")

        # Test single quotes stripped
        with patch.dict(os.environ, {"GEMINI_API_KEY": " 'AIzaSySingleQuotesKey' "}):
            key = get_gemini_api_key()
            self.assertEqual(key, "AIzaSySingleQuotesKey")

        # Test GOOGLE_API_KEY fallback
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "AIzaSyGoogleKey123"}):
            key = get_gemini_api_key()
            self.assertEqual(key, "AIzaSyGoogleKey123")

        # Test nested secrets dictionary extraction
        from llm import _extract_key_from_dict_or_secrets
        nested_secrets = {"gemini": {"api_key": "AIzaSyNestedTableKey"}}
        extracted = _extract_key_from_dict_or_secrets(nested_secrets)
        self.assertEqual(extracted, "AIzaSyNestedTableKey")

    def test_sanitize_error_redacts_keys(self):
        """Never print or expose the API key in logs or debug expander."""
        from llm import sanitize_error
        import os

        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyFakeSecretKey1234567890123456"}):
            raw_msg = "Error 403 on https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyFakeSecretKey1234567890123456"
            sanitized = sanitize_error(raw_msg)
            self.assertNotIn("AIzaSyFakeSecretKey1234567890123456", sanitized)
            self.assertIn("[REDACTED_API_KEY]", sanitized)

    def test_live_ai_needed_error_details(self):
        """Step 2: LiveAINeededError holds debug details while str() returns the standard prompt."""
        from llm import LiveAINeededError
        err = LiveAINeededError("Live AI is needed for this topic. Try Python loops.", debug_details="RuntimeError: 403 Forbidden")
        self.assertEqual(str(err), "Live AI is needed for this topic. Try Python loops.")
        self.assertEqual(err.debug_details, "RuntimeError: 403 Forbidden")

    def test_gemini_test_connection_and_model_config(self):
        """Step 4 & 5: Test connection helper and generation config."""
        from llm import llm_service
        import os

        # When key is missing or placeholder
        with patch.dict(os.environ, {"GEMINI_API_KEY": "paste_your_key_here"}):
            success, msg = llm_service.test_connection()
            self.assertFalse(success)
            self.assertIn("not configured", msg)

        # When mock call succeeds
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaFakeValidKeyForTesting1234567"}):
            with patch.object(llm_service, "_call_gemini_raw", return_value='{"status": "ok"}'):
                success, msg = llm_service.test_connection()
                self.assertTrue(success)
                self.assertEqual(msg, "Success")

    def test_gemini_success_does_not_call_groq(self):
        """When Gemini succeeds, Groq must NOT be called."""
        sample_lesson = get_fallback_lesson(Profile(topic="Python loops", minutes=15))
        with patch.object(llm_service, "_call_gemini_raw", return_value=sample_lesson.model_dump_json()) as mock_gemini, \
             patch.object(llm_service, "_call_groq_raw") as mock_groq:
            p = Profile(name="Tester", topic="Python loops", minutes=15)
            lesson = llm_service.generate_lesson_llm(p)
            self.assertEqual(mock_gemini.call_count, 1)
            self.assertEqual(mock_groq.call_count, 0)
            self.assertEqual(lesson.source, "Live AI")

    def test_gemini_rate_limit_or_api_error_triggers_groq_fallback(self):
        """When Gemini returns a rate-limit/API error, automatically try Groq for lesson generation."""
        sample_lesson = get_fallback_lesson(Profile(topic="Python loops", minutes=15))
        with patch.object(llm_service, "_call_gemini_raw", side_effect=RuntimeError("429 ResourceExhausted: Rate limit exceeded")) as mock_gemini, \
             patch.object(llm_service, "_call_groq_raw", return_value=sample_lesson.model_dump_json()) as mock_groq:
            p = Profile(name="Tester", topic="Python loops", minutes=15)
            lesson = llm_service.generate_lesson_llm(p)
            self.assertEqual(mock_gemini.call_count, 1)
            self.assertEqual(mock_groq.call_count, 1)
            self.assertEqual(lesson.source, "Live AI")

    def test_groq_fallback_for_concepts_and_quiz(self):
        """When Gemini returns rate-limit/API errors, Groq handles concepts and quiz generation."""
        sample_concepts = [
            {"concept_id": "qubits", "name": "Qubits", "common_mistake": "Assuming qubits are binary bits"},
            {"concept_id": "superposition", "name": "Superposition", "common_mistake": "Confusing superposition with probability"},
            {"concept_id": "entanglement", "name": "Entanglement", "common_mistake": "Thinking entanglement enables FTL communication"},
        ]
        # 1. Concepts fallback
        with patch.object(llm_service, "_call_gemini_raw", side_effect=RuntimeError("503 Service Unavailable")) as mock_gemini, \
             patch.object(llm_service, "_call_groq_raw", return_value=json.dumps(sample_concepts)) as mock_groq:
            concepts = llm_service.generate_concepts("Quantum Mechanics", level="beginner")
            self.assertEqual(mock_gemini.call_count, 1)
            self.assertEqual(mock_groq.call_count, 1)
            self.assertEqual(len(concepts), 3)

        # 2. Quiz fallback
        valid_quiz = get_fallback_quiz(["qubits", "superposition"])
        with patch.object(llm_service, "_call_gemini_raw", side_effect=RuntimeError("429 RateLimit")) as mock_gemini, \
             patch.object(llm_service, "_call_groq_raw", return_value=valid_quiz.model_dump_json()) as mock_groq:
            quiz = llm_service.generate_quiz_llm(["qubits", "superposition"], topic="Quantum Mechanics", concepts=sample_concepts)
            self.assertEqual(mock_gemini.call_count, 1)
            self.assertEqual(mock_groq.call_count, 1)
            self.assertEqual(quiz.source, "Live AI")
            self.assertEqual(len(quiz.questions), 5)

    def test_groq_key_extraction_and_sanitization(self):
        """Verify get_groq_api_key handles whitespace, quotes, secrets, and sanitizes keys."""
        from llm import get_groq_api_key, _extract_groq_key_from_dict_or_secrets, sanitize_error

        # Placeholder ignored
        with patch.dict(os.environ, {"GROQ_API_KEY": "paste_your_key_here"}):
            self.assertIsNone(get_groq_api_key())

        # Whitespace and quotes stripped
        with patch.dict(os.environ, {"GROQ_API_KEY": '  "gsk_TestApiKey1234567890abcdef"  '}):
            key = get_groq_api_key()
            self.assertEqual(key, "gsk_TestApiKey1234567890abcdef")

        # Nested secrets dictionary extraction
        nested_secrets = {"groq": {"api_key": "gsk_NestedTableKey1234567890abcdef"}}
        extracted = _extract_groq_key_from_dict_or_secrets(nested_secrets)
        self.assertEqual(extracted, "gsk_NestedTableKey1234567890abcdef")

        # Key sanitization
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_SecretKey1234567890abcdef"}):
            err_msg = "Error with key gsk_SecretKey1234567890abcdef on api.groq.com"
            sanitized = sanitize_error(err_msg)
            self.assertNotIn("gsk_SecretKey1234567890abcdef", sanitized)
            self.assertIn("[REDACTED_API_KEY]", sanitized)


if __name__ == "__main__":
    unittest.main()
