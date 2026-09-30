from __future__ import annotations

import uuid
from typing import Optional
from schemas import Profile, Lesson, Quiz, Question, Answer, Result
import db
from llm import llm_service, get_fallback_quiz
from engine import engine


def generate_lesson(profile: Profile, weak_concept: Optional[str] = None) -> Lesson:
    """
    Generates a structured Python loops lesson with 6 sections:
    intro, explain, example, practice, quiz, recap.
    Sum of section minutes strictly equals profile.minutes.
    The example section has animation={'component': 'range_viz', 'start': 0, 'end': 5}.
    Calls Gemini with JSON mode, temperature 0.3, with fallback on failure.
    Saves session to SQLite.
    """
    # If weak_concept is not explicitly passed, inspect db for any concept with mastery < 0.6
    if weak_concept is None:
        all_masteries = db.get_all_mastery()
        weak_concept = engine.determine_weak_concept(all_masteries)

    lesson = llm_service.generate_lesson_llm(profile=profile, weak_concept=weak_concept)

    # Record session to SQLite
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    db.save_session(session_id=session_id, user_id=profile.user_id, topic=lesson.topic)

    return lesson


def generate_quiz(concept_ids: list[str]) -> Quiz:
    """
    Generates a 5-question quiz on Python loops.
    Restricts questions strictly to the allowed concept_ids.
    Persists questions into SQLite questions table.
    """
    target_concepts = concept_ids if concept_ids else ["range_bounds", "loop_body"]

    quiz = llm_service.generate_quiz_llm(allowed_concept_ids=target_concepts)

    # Persist questions to SQLite
    db.save_questions(quiz.questions)

    return quiz


def submit_answers(answers: list[Answer]) -> Result:
    """
    Scores submitted answers against each question's correct_index.
    Updates concept mastery in SQLite: mastery += 0.3 * (outcome - mastery).
    Identifies weak_concept (lowest mastery concept below 0.6).
    Computes next_focus (one-line string).
    """
    # Load questions from SQLite
    questions_dict: dict[str, Question] = {}
    fallback_pool = {q.id: q for q in get_fallback_quiz(["range_bounds", "loop_body"]).questions}

    for ans in answers:
        q = db.get_question(ans.question_id)
        if not q and ans.question_id in fallback_pool:
            q = fallback_pool[ans.question_id]
            db.save_question(q)
        if q:
            questions_dict[q.id] = q

    # If answers list didn't include some questions, also pull any known questions
    if not questions_dict:
        questions_dict = fallback_pool
        db.save_questions(list(fallback_pool.values()))

    # Score and update mastery via engine
    result = engine.score_and_update(answers=answers, questions_dict=questions_dict)
    return result
