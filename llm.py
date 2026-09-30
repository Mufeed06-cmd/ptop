from __future__ import annotations

import json
import os
from typing import Optional
from schemas import Profile, Lesson, LessonSection, Quiz, Question


def _distribute_minutes(total_minutes: int, num_sections: int = 6) -> list[int]:
    """Distributes total_minutes across 6 sections so the sum equals total_minutes."""
    if total_minutes <= 0:
        return [0] * num_sections
    if total_minutes < num_sections:
        res = [0] * num_sections
        for i in range(total_minutes):
            res[i] = 1
        return res

    weights = [1, 3, 3, 4, 2, 2]
    total_weight = sum(weights)
    alloc = [max(1, int(total_minutes * w / total_weight)) for w in weights]
    diff = total_minutes - sum(alloc)
    priority = [3, 2, 1, 4, 5, 0]
    idx = 0
    while diff > 0:
        alloc[priority[idx % len(priority)]] += 1
        diff -= 1
        idx += 1
    while diff < 0:
        target = priority[idx % len(priority)]
        if alloc[target] > 1:
            alloc[target] -= 1
            diff += 1
        idx += 1
        if idx > 50:
            alloc[0] += diff
            break
    return alloc


def _distribute_minutes_adaptive(total_minutes: int, num_sections: int = 6) -> list[int]:
    """
    Distributes total_minutes across 6 sections for adaptive lessons:
    - Intro is shorter: strictly 1 min (for total_minutes >= 6)
    - Explain and Example get the bulk of the time
    - Total still strictly equals total_minutes
    """
    if total_minutes <= 0:
        return [0] * num_sections
    if total_minutes < num_sections:
        res = [0] * num_sections
        for i in range(total_minutes):
            res[i] = 1
        return res

    # Section 0 (Intro): 1 min
    # Section 4 (Quiz): 1 min
    # Section 5 (Recap): 1 min
    fixed = 3
    remaining = total_minutes - fixed
    practice = max(1, int(round(remaining * 0.2)))
    rem_core = remaining - practice
    explain = max(2, rem_core // 2)
    example = max(2, rem_core - explain)

    alloc = [1, explain, example, practice, 1, 1]
    diff = total_minutes - sum(alloc)
    if diff > 0:
        alloc[1] += diff // 2
        alloc[2] += diff - (diff // 2)
    elif diff < 0:
        alloc[2] += diff
    return alloc


def get_fallback_adaptive_lesson(profile: Profile, weak_concept: str) -> Lesson:
    """Returns a completely distinct hardcoded adaptive remedial lesson focusing on the diagnosed weak concept."""
    total_minutes = profile.minutes
    durations = _distribute_minutes_adaptive(total_minutes, 6)

    sections = [
        LessonSection(
            id="sec_1_intro",
            type="intro",
            title=f"Adaptive Diagnostic Focus: {weak_concept}",
            minutes=durations[0],
            content=(
                f"In this focused adaptive session, we target the specific mental model behind `{weak_concept}`.\n\n"
                "Instead of re-reading general theory, we isolate the exact boundary mechanics "
                "where cognitive slips occur."
            ),
        ),
        LessonSection(
            id="sec_2_explain",
            type="explain",
            title="Step-by-Step Execution Trace: range(0, 5)",
            minutes=durations[1],
            content=(
                "The most common off-by-one mistake occurs because humans count inclusively, "
                "whereas Python evaluates `range(start, stop)` as the half-open interval `[start, stop)`.\n\n"
                "Here is the exact step-by-step trace of what the Python interpreter does:\n\n"
                "| Iteration / Step | Current `i` Value | Condition Checked | Loop Body Runs? | What Happens |\n"
                "|:---:|:---:|:---:|:---:|:---|\n"
                "| **Step 1** | `i = 0` (Start) | `0 < 5` (True) | ✅ **Runs** | Loop body executes with `i = 0` |\n"
                "| **Step 2** | `i = 1` | `1 < 5` (True) | ✅ **Runs** | Loop body executes with `i = 1` |\n"
                "| **Step 3** | `i = 2` | `2 < 5` (True) | ✅ **Runs** | Loop body executes with `i = 2` |\n"
                "| **Step 4** | `i = 3` | `3 < 5` (True) | ✅ **Runs** | Loop body executes with `i = 3` |\n"
                "| **Step 5** | `i = 4` | `4 < 5` (True) | ✅ **Runs** | Loop body executes with `i = 4` |\n"
                "| **Step 6** | `i = 5` (Stop Bound) | `5 < 5` (False) | ❌ **Terminates** | **5 is never reached** — loop exits immediately |\n\n"
                "**The Golden Rule:** The condition tested on each iteration is `i < stop`. "
                "The moment `i` reaches 5, the condition evaluates to `False`. Thus, **5 is never reached** inside the loop body!"
            ),
            code="# Python half-open interval:\nfor i in range(0, 5):\n    print(i)  # Produces 0, 1, 2, 3, 4\n# 5 is never reached!",
        ),
        LessonSection(
            id="sec_3_example",
            type="example",
            title="Visualizing Excluded Stop Bound: range(0, 5)",
            minutes=durations[2],
            content=(
                "Interact with the range strip below. Notice how the stop boundary `5` is highlighted as **STOP (EXCL)**. "
                "It serves as a guard wall that halts execution before 5 can enter the loop body."
            ),
            animation={"component": "range_viz", "start": 0, "end": 5},
            code="desired_count = 5\nfor i in range(0, desired_count):\n    print(f'Processing item: {i}')\n# Output halts before reaching 5!",
        ),
        LessonSection(
            id="sec_4_practice",
            type="practice",
            title="Targeted Practice: Reaching the Stop Value",
            minutes=durations[3],
            content=(
                "**Exercise:** If you need your loop to process numbers 0 through 5 (including 5), "
                "how should you write the `range()` call?\n\n"
                "- ❌ `range(0, 5)` stops at 4.\n"
                "- ✅ `range(0, 6)` stops before 6, including 5!\n\n"
                "Always add `+ 1` to the desired ending number if you need it included."
            ),
            code="# Fix: Add +1 to include 5\nfor n in range(0, 5 + 1):\n    print(n, end=' ')  # Prints: 0 1 2 3 4 5",
        ),
        LessonSection(
            id="sec_5_quiz",
            type="quiz",
            title="Concept Verification",
            minutes=durations[4],
            content="Next: a 5-question checkpoint on range bounds and loop bodies.",
        ),
        LessonSection(
            id="sec_6_recap",
            type="recap",
            title="Adaptive Sprint Recap: Exclusivity Invariant",
            minutes=durations[5],
            content=(
                "Summary:\n"
                "- In Python, `range(start, stop)` NEVER includes `stop`. **5 is never reached** in `range(0, 5)`.\n"
                "- To include $N$, specify $N + 1$ as the stop value.\n"
                "- Indented statements define the loop body."
            ),
        ),
    ]

    return Lesson(
        id=f"lesson_adaptive_{weak_concept}",
        topic=f"Python Loops Remediation: {weak_concept}",
        total_minutes=total_minutes,
        sections=sections,
        weak_concept=weak_concept,
        language=profile.language,
    )


def get_fallback_lesson(profile: Profile, weak_concept: Optional[str] = None) -> Lesson:
    """Returns a hardcoded fallback Python loops lesson conforming strictly to all requirements."""
    if weak_concept:
        return get_fallback_adaptive_lesson(profile, weak_concept)

    total_minutes = profile.minutes
    durations = _distribute_minutes(total_minutes, 6)

    greeting = f"Welcome, {profile.name}! " if profile.name and profile.name.strip() and profile.name.lower() != "alex" else ""

    sections = [
        LessonSection(
            id="sec_1_intro",
            type="intro",
            title="Introduction to Python Loops",
            minutes=durations[0],
            content=(
                f"{greeting}In this lesson, we study Python `for` loops.\n"
                "Loops allow you to iterate through sequences cleanly without repeating code."
            ),
        ),
        LessonSection(
            id="sec_2_explain",
            type="explain",
            title="Understanding range() and Loop Execution",
            minutes=durations[1],
            content=(
                "Python's `range(start, stop)` function produces integers starting from `start` "
                "and terminating strictly before `stop`.\n\n"
                "- **Start Bound**: Inclusive\n"
                "- **Stop Bound**: Exclusive\n"
                "- **Loop Body**: Code indented inside executes on each step."
            ),
            code="for i in range(0, 5):\n    print('Iteration:', i)",
        ),
        LessonSection(
            id="sec_3_example",
            type="example",
            title="Step-by-Step Visualization of range(0, 5)",
            minutes=durations[2],
            content=(
                "Trace each iteration of `range(0, 5)`. Notice that index 5 is excluded!\n"
                "The values yielded are: 0, 1, 2, 3, and 4."
            ),
            animation={"component": "range_viz", "start": 0, "end": 5},
            code="for i in range(0, 5):\n    print(i)",
        ),
        LessonSection(
            id="sec_4_practice",
            type="practice",
            title="Interactive Loop Practice",
            minutes=durations[3],
            content=(
                "Practice exercise: Accumulate the sum of integers from 1 to 5 inclusive using `range(1, 6)`."
            ),
            code="total = 0\nfor x in range(1, 6):\n    total += x\nprint('Total:', total)",
        ),
        LessonSection(
            id="sec_5_quiz",
            type="quiz",
            title="Checkpoint Preparation",
            minutes=durations[4],
            content="Next: a 5-question checkpoint on range bounds and loop bodies.",
        ),
        LessonSection(
            id="sec_6_recap",
            type="recap",
            title="Lesson Recap & Key Rules",
            minutes=durations[5],
            content=(
                "Key Takeaways:\n"
                "- `range(start, stop)` generates numbers up to `stop - 1`.\n"
                "- Loop statements must be indented inside the body.\n"
                "- To include N, set stop to N + 1."
            ),
        ),
    ]

    return Lesson(
        id="lesson_python_loops_fallback",
        topic="Python For Loops & range()",
        total_minutes=total_minutes,
        sections=sections,
        weak_concept=weak_concept,
        language=profile.language,
    )


def get_fallback_quiz(allowed_concept_ids: list[str]) -> Quiz:
    """Returns a hardcoded fallback 5-question quiz using only the allowed concept_ids."""
    raw_pool = [
        Question(
            id="q1",
            concept_id="range_bounds",
            question="What sequence of numbers does `range(0, 5)` generate?",
            options=["0, 1, 2, 3, 4", "0, 1, 2, 3, 4, 5", "1, 2, 3, 4, 5", "1, 2, 3, 4"],
            correct_index=0,
            explanation="In Python, range(start, stop) starts at start (0) and stops before stop (5).",
        ),
        Question(
            id="q2",
            concept_id="loop_body",
            question="How many times will this loop print 'Hello'?\n\n```python\nfor i in range(3):\n    print('Hello')\n```",
            options=["2 times", "3 times", "4 times", "0 times"],
            correct_index=1,
            explanation="The loop executes for i=0, i=1, and i=2, totaling 3 executions.",
        ),
        Question(
            id="q3",
            concept_id="range_bounds",
            question="What is the output of `list(range(2, 6))`?",
            options=["[2, 3, 4, 5, 6]", "[2, 3, 4, 5]", "[3, 4, 5, 6]", "[2, 4, 6]"],
            correct_index=1,
            explanation="The range begins at 2 (inclusive) and stops before 6 (exclusive): [2, 3, 4, 5].",
        ),
        Question(
            id="q4",
            concept_id="loop_body",
            question="What is the final value of `total`?\n\n```python\ntotal = 0\nfor x in [1, 2, 3]:\n    total += x\n```",
            options=["3", "5", "6", "0"],
            correct_index=2,
            explanation="The body adds each item: 0 + 1 + 2 + 3 = 6.",
        ),
        Question(
            id="q5",
            concept_id="range_bounds",
            question="Which expression generates integers from 1 through 5 inclusive: `[1, 2, 3, 4, 5]`?",
            options=["range(1, 5)", "range(1, 6)", "range(5)", "range(0, 5)"],
            correct_index=1,
            explanation="Because the stop bound is exclusive, stop must be 6 to include 5.",
        ),
    ]

    allowed_set = set(allowed_concept_ids) if allowed_concept_ids else {"range_bounds", "loop_body"}
    filtered = [q for q in raw_pool if q.concept_id in allowed_set]
    if len(filtered) < 5:
        # If filtered set is smaller than 5, re-map concept_ids to conform strictly to allowed_set
        fallback_concept = list(allowed_set)[0]
        adjusted = []
        for q in raw_pool:
            cid = q.concept_id if q.concept_id in allowed_set else fallback_concept
            adjusted.append(
                Question(
                    id=q.id,
                    concept_id=cid,
                    question=q.question,
                    options=q.options,
                    correct_index=q.correct_index,
                    explanation=q.explanation,
                )
            )
        filtered = adjusted[:5]

    return Quiz(
        id="quiz_python_loops_fallback",
        topic="Python Loops Assessment",
        concept_ids=list(allowed_set),
        questions=filtered[:5],
    )


class LLMService:
    """
    Interacts with Google Gemini with:
    - Temperature 0.3
    - JSON response mode
    - Pydantic validation
    - Single retry on validation error
    - Hardcoded fallback on persistent error
    - API key read strictly from GEMINI_API_KEY environment variable
    """

    def __init__(self):
        self._genai = None
        self._model = None
        self._setup_client()

    def _setup_client(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
            self._model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3,
                },
            )
        except Exception:
            self._model = None

    @property
    def is_configured(self) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY")) and self._model is not None

    def _call_gemini_raw(self, prompt: str) -> str:
        """Invokes Gemini with configured temperature 0.3 and JSON response mode."""
        if not self._model:
            self._setup_client()
        if not self._model:
            raise RuntimeError("Gemini client is not configured (missing or invalid GEMINI_API_KEY).")

        response = self._model.generate_content(prompt)
        return response.text

    def generate_lesson_llm(self, profile: Profile, weak_concept: Optional[str] = None) -> Lesson:
        """
        Calls Gemini to generate a Lesson.
        Prompt requirements:
        - "Explain in {language}. Keep code and technical terms in English."
        - If weak_concept is set:
          "The student struggled with {weak_concept}. Use a step-by-step trace explanation and address the common mistake."
        - JSON response mode, temperature 0.3, retry once if invalid, else fallback.
        """
        language = profile.language or "English"

        prompt_parts = [
            f"You are an expert Python programming instructor creating a structured lesson for learner '{profile.name}'.",
            f"Topic: Python For Loops and range(). Total lesson minutes: {profile.minutes}.",
            f"Explain in {language}. Keep code and technical terms in English.",
        ]

        if weak_concept:
            prompt_parts.append(
                f"The student struggled with {weak_concept}. Use a step-by-step trace explanation and address the common mistake."
            )

        prompt_parts.append(
            """
Return a valid JSON object matching this schema:
{
  "id": "lesson_generated",
  "topic": "Python For Loops",
  "total_minutes": <int>,
  "weak_concept": <string or null>,
  "language": "<language>",
  "sections": [
    {
      "id": "sec_1",
      "type": "intro",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>
    },
    {
      "id": "sec_2",
      "type": "explain",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>,
      "code": "<python code>"
    },
    {
      "id": "sec_3",
      "type": "example",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>,
      "animation": {"component": "range_viz", "start": 0, "end": 5},
      "code": "<python code>"
    },
    {
      "id": "sec_4",
      "type": "practice",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>,
      "code": "<python code>"
    },
    {
      "id": "sec_5",
      "type": "quiz",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>
    },
    {
      "id": "sec_6",
      "type": "recap",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>
    }
  ]
}
Exactly 6 sections (types: intro, explain, example, practice, quiz, recap).
The example section must have animation: {"component": "range_viz", "start": 0, "end": 5}.
"""
        )

        initial_prompt = "\n".join(prompt_parts)

        # First attempt
        try:
            raw_text = self._call_gemini_raw(initial_prompt)
            data = json.loads(raw_text)
            lesson = Lesson.model_validate(data)
            return self._normalize_lesson(lesson, profile, weak_concept)
        except Exception as first_error:
            # Retry once with error message
            try:
                retry_prompt = (
                    f"{initial_prompt}\n\n"
                    f"Your previous output failed validation with error: {str(first_error)}.\n"
                    "Please regenerate and ensure the output is strictly valid JSON conforming to the schema."
                )
                raw_text_retry = self._call_gemini_raw(retry_prompt)
                data_retry = json.loads(raw_text_retry)
                lesson = Lesson.model_validate(data_retry)
                return self._normalize_lesson(lesson, profile, weak_concept)
            except Exception:
                # Still failed, return hardcoded fallback
                return get_fallback_lesson(profile, weak_concept)

    def _normalize_lesson(self, lesson: Lesson, profile: Profile, weak_concept: Optional[str]) -> Lesson:
        """Ensures minute invariants and required animation component on parsed lessons."""
        if weak_concept:
            durations = _distribute_minutes_adaptive(profile.minutes, len(lesson.sections) or 6)
        else:
            durations = _distribute_minutes(profile.minutes, len(lesson.sections) or 6)

        for idx, sec in enumerate(lesson.sections):
            if idx < len(durations):
                sec.minutes = durations[idx]
            if sec.type == "example" and not sec.animation:
                sec.animation = {"component": "range_viz", "start": 0, "end": 5}
            if sec.type == "quiz":
                sec.content = "Next: a 5-question checkpoint on range bounds and loop bodies."

        lesson.total_minutes = profile.minutes
        lesson.weak_concept = weak_concept
        lesson.language = profile.language
        return lesson

    def generate_quiz_llm(self, allowed_concept_ids: list[str]) -> Quiz:
        """
        Calls Gemini to generate a 5-question Quiz.
        Quiz questions must use only the allowed concept_ids.
        JSON response mode, temperature 0.3, retry once if invalid, else fallback.
        """
        allowed_list_str = ", ".join(f"'{cid}'" for cid in allowed_concept_ids)

        initial_prompt = f"""
You are an expert Python educational assessment designer.
Generate a 5-question multiple choice quiz on Python loops.
CRITICAL CONSTRAINT: Quiz questions must use only the allowed concept_ids: [{allowed_list_str}]. Do NOT use any other concept_id.
Each question must have 4 options, a 0-based integer 'correct_index' (0, 1, 2, or 3), and an explanation.

Return a valid JSON object matching this schema:
{{
  "id": "quiz_generated",
  "topic": "Python Loops Checkpoint",
  "concept_ids": {json.dumps(allowed_concept_ids)},
  "questions": [
    {{
      "id": "q1",
      "concept_id": "<must be one of: {allowed_list_str}>",
      "question": "<question text>",
      "options": ["<option 0>", "<option 1>", "<option 2>", "<option 3>"],
      "correct_index": <int 0-3>,
      "explanation": "<detailed explanation>"
    }}
  ]
}}
Ensure exactly 5 questions are provided.
"""

        # First attempt
        try:
            raw_text = self._call_gemini_raw(initial_prompt)
            data = json.loads(raw_text)
            quiz = Quiz.model_validate(data)
            return self._validate_and_sanitize_quiz(quiz, allowed_concept_ids)
        except Exception as first_error:
            # Retry once with error message
            try:
                retry_prompt = (
                    f"{initial_prompt}\n\n"
                    f"Your previous response was invalid. Error: {str(first_error)}.\n"
                    "Ensure valid JSON with 5 questions using ONLY the allowed concept_ids."
                )
                raw_text_retry = self._call_gemini_raw(retry_prompt)
                data_retry = json.loads(raw_text_retry)
                quiz = Quiz.model_validate(data_retry)
                return self._validate_and_sanitize_quiz(quiz, allowed_concept_ids)
            except Exception:
                return get_fallback_quiz(allowed_concept_ids)

    def _validate_and_sanitize_quiz(self, quiz: Quiz, allowed_concept_ids: list[str]) -> Quiz:
        """Enforces that all quiz questions use only the allowed concept_ids and have 5 questions."""
        allowed_set = set(allowed_concept_ids)
        valid_questions = []

        for q in quiz.questions:
            if q.concept_id not in allowed_set:
                # Force to first allowed concept_id if deviated
                q.concept_id = allowed_concept_ids[0]
            valid_questions.append(q)

        # If fewer than 5, supplement with fallback
        if len(valid_questions) < 5:
            fallback = get_fallback_quiz(allowed_concept_ids)
            for fq in fallback.questions:
                if len(valid_questions) >= 5:
                    break
                if not any(eq.id == fq.id for eq in valid_questions):
                    valid_questions.append(fq)

        quiz.questions = valid_questions[:5]
        quiz.concept_ids = allowed_concept_ids
        return quiz


llm_service = LLMService()
