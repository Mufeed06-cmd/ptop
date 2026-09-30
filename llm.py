from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Optional
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
        source="Fallback",
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
        source="Fallback",
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
        source="Fallback",
    )


CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def is_python_loops_topic(topic: Optional[str]) -> bool:
    """Returns True if the topic refers to Python loops."""
    if not topic:
        return True
    t = topic.lower().strip()
    return ("python" in t and "loop" in t) or t in ["python loops", "python - loops", "loops"]


def get_gemini_api_key() -> Optional[str]:
    """
    Retrieves the Gemini API key from:
    1. st.secrets["GEMINI_API_KEY"] (if running in Streamlit with secrets configured)
    2. os.getenv("GEMINI_API_KEY") (or os.environ.get("GEMINI_API_KEY"))
    Strips any whitespace or surrounding quotes (' or ").
    Returns None if missing or placeholder. Never prints the key.
    """
    raw_key: Optional[str] = None

    # Check Streamlit secrets first
    try:
        import streamlit as st
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                raw_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
        if not raw_key:
            try:
                if hasattr(st, "secrets") and hasattr(st.secrets, "get"):
                    raw_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass
    except Exception:
        pass

    # Fall back to environment variable
    if not raw_key:
        raw_key = os.getenv("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if not raw_key:
        return None

    # Strip whitespace
    key = str(raw_key).strip()

    # Strip single or double quotes at the ends
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()
    key = key.strip("\"' \t\r\n")

    if not key or key == "paste_your_key_here":
        return None

    # Also synchronize to os.environ so any underlying SDK/subprocesses have it
    os.environ["GEMINI_API_KEY"] = key
    return key


def sanitize_error(err: Any) -> str:
    """Removes any API keys from error messages before logging or rendering."""
    msg = str(err)
    key = get_gemini_api_key()
    if key and key in msg:
        msg = msg.replace(key, "[REDACTED_API_KEY]")
    msg = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED_API_KEY]', msg)
    return msg


class LiveAINeededError(Exception):
    """Raised when live AI is needed for a topic but Gemini is unavailable or failed."""
    def __init__(
        self,
        message: str = "Live AI is needed for this topic. Try Python loops.",
        debug_details: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.debug_details = debug_details or message

    def __str__(self) -> str:
        return self.message


PYTHON_LOOPS_CONCEPTS = [
    {
        "concept_id": "range_bounds",
        "name": "Range Bounds & Exclusivity",
        "common_mistake": "Believing range(0, 5) includes 5 instead of stopping at 4",
    },
    {
        "concept_id": "loop_body",
        "name": "Loop Body Execution & Indentation",
        "common_mistake": "Misunderstanding which indented statements execute repeatedly within the loop",
    },
    {
        "concept_id": "loop_variables",
        "name": "Loop Variable Mutation",
        "common_mistake": "Modifying loop variable inside loop expecting it to change iteration progression",
    },
]


def _get_concepts_cache_path(topic: str, level: str, goal: Optional[str]) -> Path:
    t = re.sub(r'[^a-zA-Z0-9]+', '_', topic.lower()).strip('_')
    lev = re.sub(r'[^a-zA-Z0-9]+', '_', level.lower()).strip('_')
    g = re.sub(r'[^a-zA-Z0-9]+', '_', (goal or "default").lower()).strip('_')
    h = hashlib.sha256(f"{topic}|{level}|{goal}".lower().encode()).hexdigest()[:8]
    return CACHE_DIR / f"concepts_{t}_{lev}_{g}_{h}.json"


def load_cached_concepts(topic: str, level: str, goal: Optional[str]) -> Optional[list[dict[str, str]]]:
    path = _get_concepts_cache_path(topic, level, goal)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) == 3:
            return data
    except Exception:
        pass
    return None


def save_cached_concepts(topic: str, level: str, goal: Optional[str], concepts: list[dict[str, str]]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _get_concepts_cache_path(topic, level, goal)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(concepts, f, indent=2)
    except Exception:
        pass


def _get_lesson_cache_path(topic: str, level: str, language: str, minutes: int, weak_concept: Optional[str]) -> Path:
    t = re.sub(r'[^a-zA-Z0-9]+', '_', topic.lower()).strip('_')
    lev = re.sub(r'[^a-zA-Z0-9]+', '_', level.lower()).strip('_')
    lang = re.sub(r'[^a-zA-Z0-9]+', '_', language.lower()).strip('_')
    wc = re.sub(r'[^a-zA-Z0-9]+', '_', (weak_concept or "none").lower()).strip('_')
    raw = f"{t}_{lev}_{lang}_{minutes}m_{wc}"
    h = hashlib.sha256(f"{topic}|{level}|{language}|{minutes}|{weak_concept}".lower().encode()).hexdigest()[:8]
    return CACHE_DIR / f"lesson_{raw}_{h}.json"


def load_cached_lesson(topic: str, level: str, language: str, minutes: int, weak_concept: Optional[str]) -> Optional[Lesson]:
    path = _get_lesson_cache_path(topic, level, language, minutes, weak_concept)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        lesson = Lesson.model_validate(data["lesson"])
        lesson.source = "Cached"
        return lesson
    except Exception:
        return None


def save_cached_lesson(topic: str, level: str, language: str, minutes: int, weak_concept: Optional[str], lesson: Lesson) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _get_lesson_cache_path(topic, level, language, minutes, weak_concept)
        payload = {
            "topic": topic,
            "level": level,
            "language": language,
            "minutes": minutes,
            "weak_concept": weak_concept,
            "lesson": lesson.model_dump(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


def _validate_concepts_data(data: Any) -> list[dict[str, str]]:
    if isinstance(data, dict):
        data = data.get("concepts", data.get("items", list(data.values())[0] if data else []))
    if not isinstance(data, list) or len(data) != 3:
        raise ValueError(f"Expected exactly 3 concepts, got {len(data) if isinstance(data, list) else type(data)}")
    res = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Concept item {i+1} must be a dict")
        cid = str(item.get("concept_id") or "").strip()
        name = str(item.get("name") or "").strip()
        mistake = str(item.get("common_mistake") or "").strip()
        if not cid or not name or not mistake:
            raise ValueError(f"Concept {i+1} missing required keys (concept_id, name, common_mistake)")
        snake_cid = re.sub(r'[^a-zA-Z0-9]+', '_', cid).strip('_').lower()
        if not snake_cid:
            snake_cid = f"concept_{i+1}"
        res.append({
            "concept_id": snake_cid,
            "name": name,
            "common_mistake": mistake,
        })
    return res


def _validate_quiz_rules(quiz: Quiz, allowed_concept_ids: list[str]) -> tuple[bool, str]:
    """Validates that quiz conforms strictly to all 5 questions, 4 options, and allowed concept_ids."""
    allowed_set = set(allowed_concept_ids)
    if len(quiz.questions) != 5:
        return False, f"Expected exactly 5 questions, got {len(quiz.questions)}"
    for idx, q in enumerate(quiz.questions):
        if q.concept_id not in allowed_set:
            return False, f"Question {idx+1} ({q.id}) has concept_id '{q.concept_id}' not in allowed {allowed_concept_ids}"
        if not q.options or len(q.options) != 4:
            return False, f"Question {idx+1} ({q.id}) must have exactly 4 options, got {len(q.options) if q.options else 0}"
        if not (0 <= q.correct_index < 4):
            return False, f"Question {idx+1} ({q.id}) correct_index {q.correct_index} is out of bounds (0-3)"
    return True, ""


class LLMService:
    """
    Interacts with Google Gemini with:
    - Temperature 0.3
    - JSON response mode (response_mime_type="application/json")
    - Pydantic validation
    - Single retry on validation error
    - Hardcoded fallback on persistent error
    - API key read safely from st.secrets and os.getenv with whitespace and quote stripping
    """

    def __init__(self):
        self._genai = None
        self._model = None
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self._setup_error: Optional[str] = None
        self._setup_client()

    def _setup_client(self) -> None:
        api_key = get_gemini_api_key()
        if not api_key:
            self._model = None
            self._setup_error = "GEMINI_API_KEY is not configured or is a placeholder in st.secrets / os.environ."
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            generation_config = genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
            )
            self._setup_error = None
        except Exception as e:
            self._model = None
            self._setup_error = sanitize_error(f"{type(e).__name__}: {str(e)}")
            print(f"[LearnMate LOG] Failed to setup Gemini client: {self._setup_error}", flush=True)

    @property
    def is_configured(self) -> bool:
        api_key = get_gemini_api_key()
        return bool(api_key) and self._model is not None

    def test_connection(self) -> tuple[bool, str]:
        """Performs a small test call to Gemini, returning (success, message). Never leaks keys."""
        api_key = get_gemini_api_key()
        if not api_key:
            return False, "GEMINI_API_KEY is not configured or is a placeholder."

        if not self._model:
            self._setup_client()

        if not self._model:
            return False, self._setup_error or "Gemini client could not be initialized."

        try:
            # Send a tiny prompt to verify connectivity & JSON mode
            raw = self._call_gemini_raw('Respond with JSON: {"status": "ok"}')
            json.loads(raw.strip())
            return True, "Success"
        except Exception as e:
            sanitized = sanitize_error(f"{type(e).__name__}: {str(e)}")
            print(f"[LearnMate LOG] Gemini test connection failed: {sanitized}", flush=True)
            return False, sanitized

    def _call_gemini_raw(self, prompt: str) -> str:
        """Invokes Gemini with configured temperature 0.3 and JSON response mode."""
        if not self._model:
            self._setup_client()
        if not self._model:
            raise RuntimeError(f"Gemini client is not configured: {self._setup_error or 'missing or invalid GEMINI_API_KEY'}")

        try:
            response = self._model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_msg = str(e)
            if ("not found" in err_msg.lower() or "404" in err_msg) and self.model_name != "gemini-2.0-flash":
                print(f"[LearnMate LOG] Model {self.model_name} not found. Attempting fallback to gemini-2.0-flash...", flush=True)
                try:
                    self.model_name = "gemini-2.0-flash"
                    generation_config = self._genai.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.3,
                    )
                    self._model = self._genai.GenerativeModel(
                        model_name="gemini-2.0-flash",
                        generation_config=generation_config,
                    )
                    response = self._model.generate_content(prompt)
                    return response.text
                except Exception as e2:
                    sanitized2 = sanitize_error(f"{type(e2).__name__}: {str(e2)}")
                    print(f"[LearnMate LOG] Gemini fallback call failed: {sanitized2}", flush=True)
                    raise
            sanitized = sanitize_error(f"{type(e).__name__}: {str(e)}")
            print(f"[LearnMate LOG] Gemini call failed: {sanitized}", flush=True)
            raise

    def generate_concepts(self, topic: str, level: str = "beginner", goal: Optional[str] = None) -> list[dict[str, str]]:
        """
        Generates 3 items {concept_id (snake_case), name, common_mistake} for topic.
        Uses Gemini JSON mode, validates, retries once on error, caches result.
        """
        topic_clean = topic.strip()
        cached = load_cached_concepts(topic_clean, level, goal)
        if cached:
            return cached

        prompt = f"""You are an expert educational curriculum designer.
For the topic '{topic_clean}' at level '{level}' (learning goal: '{goal or "master core concepts"}'),
identify exactly 3 distinct foundational concepts required to master this topic.
For each concept, identify the single most common mistake or misconception learners make.

CRITICAL REQUIREMENT:
Return a valid JSON array of exactly 3 objects matching this schema:
[
  {{
    "concept_id": "<snake_case_identifier_lowercase_letters_and_underscores_only>",
    "name": "<Short Human-Readable Concept Name>",
    "common_mistake": "<Specific common mistake or misconception>"
  }}
]
Rules:
1. Exactly 3 items in the array.
2. concept_id must be in snake_case (e.g. inner_join, range_bounds, light_reactions).
"""

        try:
            raw_text = self._call_gemini_raw(prompt)
            data = json.loads(raw_text)
            concepts = _validate_concepts_data(data)
            save_cached_concepts(topic_clean, level, goal, concepts)
            return concepts
        except Exception as first_error:
            sanitized_first = sanitize_error(f"{type(first_error).__name__}: {str(first_error)}")
            print(f"[LearnMate LOG] generate_concepts initial attempt failed: {sanitized_first}", flush=True)
            try:
                retry_prompt = (
                    f"{prompt}\n\n"
                    f"Your previous response failed validation: {sanitized_first}.\n"
                    "Regenerate strictly valid JSON with exactly 3 objects: concept_id (snake_case), name, common_mistake."
                )
                raw_retry = self._call_gemini_raw(retry_prompt)
                data_retry = json.loads(raw_retry)
                concepts = _validate_concepts_data(data_retry)
                save_cached_concepts(topic_clean, level, goal, concepts)
                return concepts
            except Exception as second_error:
                sanitized_second = sanitize_error(f"{type(second_error).__name__}: {str(second_error)}")
                print(f"[LearnMate LOG] generate_concepts retry failed: {sanitized_second}", flush=True)
                if is_python_loops_topic(topic_clean):
                    save_cached_concepts(topic_clean, level, goal, PYTHON_LOOPS_CONCEPTS)
                    return PYTHON_LOOPS_CONCEPTS
                raise LiveAINeededError(
                    "Live AI is needed for this topic. Try Python loops.",
                    debug_details=f"{sanitized_second}\n(Initial attempt failed: {sanitized_first})",
                )

    def generate_lesson_llm(self, profile: Profile, weak_concept: Optional[str] = None, topic: Optional[str] = None) -> Lesson:
        """
        Calls Gemini to generate a 6-section Lesson for any topic.
        Prompt requirements:
        - "Explain in {language}. Keep code and technical terms in English."
        - If weak_concept is set:
          "The student struggled with {weak_concept}. Use a step-by-step trace explanation and address the common mistake."
        - JSON response mode, temperature 0.3, retry once if invalid, else fallback/error.
        - Caches by topic+level+language+minutes+weak_concept.
        """
        active_topic = topic or profile.topic or "Python loops"
        language = profile.language or "English"

        # Check cache
        cached = load_cached_lesson(active_topic, profile.skill_level, language, profile.minutes, weak_concept)
        if cached:
            cached.source = "Cached"
            return cached

        is_py = is_python_loops_topic(active_topic)

        # Get concept_ids to ground the lesson
        if is_py:
            concepts = PYTHON_LOOPS_CONCEPTS
        else:
            concepts = self.generate_concepts(active_topic, level=profile.skill_level)
        concepts_summary = "\n".join(
            f"- Concept `{c['concept_id']}` ({c['name']}): Common Mistake: {c['common_mistake']}"
            for c in concepts
        )

        is_py = is_python_loops_topic(active_topic)
        if is_py:
            prompt_parts = [
                f"You are an expert Python programming instructor creating a structured lesson for learner '{profile.name}'.",
                f"Topic: Python For Loops and range(). Total lesson minutes: {profile.minutes}.",
                f"Explain in {language}. Keep code and technical terms in English.",
            ]
        else:
            prompt_parts = [
                f"You are an expert instructor creating a structured lesson for learner '{profile.name}'.",
                f"Topic: {active_topic}. Total lesson minutes: {profile.minutes}.",
                f"Explain in {language}. Keep code and technical terms in English.",
            ]

        prompt_parts.append(f"The lesson must address these key concepts:\n{concepts_summary}")

        if weak_concept:
            prompt_parts.append(
                f"The student struggled with {weak_concept}. Use a step-by-step trace explanation and address the common mistake."
            )
            prompt_parts.append(
                f"Provide a step-by-step explanation of {weak_concept} using a different method than lesson 1 (example: analogy or trace)."
            )

        anim_instruction = (
            'The example section must have animation: {"component": "range_viz", "start": 0, "end": 5}.'
            if is_py
            else 'The example section must have animation: {"component": "step_viz", "steps": [{"title": "<step title>", "detail": "<step detail>"}]} with 3 to 6 steps.'
        )

        prompt_parts.append(
            f"""
Return a valid JSON object matching this schema:
{{
  "id": "lesson_generated",
  "topic": "{active_topic}",
  "total_minutes": {profile.minutes},
  "weak_concept": {json.dumps(weak_concept)},
  "language": "{language}",
  "sections": [
    {{
      "id": "sec_1",
      "type": "intro",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>
    }},
    {{
      "id": "sec_2",
      "type": "explain",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>,
      "code": "<code snippet or null>"
    }},
    {{
      "id": "sec_3",
      "type": "example",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>,
      "animation": {{"component": "range_viz", "start": 0, "end": 5}} if Python loops else {{"component": "step_viz", "steps": [...]}},
      "code": "<code snippet or null>"
    }},
    {{
      "id": "sec_4",
      "type": "practice",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>,
      "code": "<code snippet or null>"
    }},
    {{
      "id": "sec_5",
      "type": "quiz",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>
    }},
    {{
      "id": "sec_6",
      "type": "recap",
      "title": "<title>",
      "content": "<content>",
      "minutes": <int>
    }}
  ]
}}
Exactly 6 sections (types: intro, explain, example, practice, quiz, recap).
{anim_instruction}
"""
        )

        initial_prompt = "\n".join(prompt_parts)

        # First attempt
        try:
            raw_text = self._call_gemini_raw(initial_prompt)
            data = json.loads(raw_text)
            lesson = Lesson.model_validate(data)
            normalized = self._normalize_lesson(lesson, profile, weak_concept, topic=active_topic)
            normalized.source = "Live AI"
            save_cached_lesson(active_topic, profile.skill_level, language, profile.minutes, weak_concept, normalized)
            return normalized
        except Exception as first_error:
            sanitized_first = sanitize_error(f"{type(first_error).__name__}: {str(first_error)}")
            print(f"[LearnMate LOG] generate_lesson_llm initial attempt failed: {sanitized_first}", flush=True)
            # Retry once with error message
            try:
                retry_prompt = (
                    f"{initial_prompt}\n\n"
                    f"Your previous output failed validation with error: {sanitized_first}.\n"
                    "Please regenerate and ensure the output is strictly valid JSON conforming to the schema."
                )
                raw_text_retry = self._call_gemini_raw(retry_prompt)
                data_retry = json.loads(raw_text_retry)
                lesson = Lesson.model_validate(data_retry)
                normalized = self._normalize_lesson(lesson, profile, weak_concept, topic=active_topic)
                normalized.source = "Live AI"
                save_cached_lesson(active_topic, profile.skill_level, language, profile.minutes, weak_concept, normalized)
                return normalized
            except Exception as second_error:
                sanitized_second = sanitize_error(f"{type(second_error).__name__}: {str(second_error)}")
                print(f"[LearnMate LOG] generate_lesson_llm retry failed: {sanitized_second}", flush=True)
                if is_py:
                    lesson = get_fallback_lesson(profile, weak_concept)
                    lesson.source = "Fallback"
                    return lesson
                raise LiveAINeededError(
                    "Live AI is needed for this topic. Try Python loops.",
                    debug_details=f"{sanitized_second}\n(Initial attempt failed: {sanitized_first})",
                )

    def _normalize_lesson(self, lesson: Lesson, profile: Profile, weak_concept: Optional[str], topic: str = "Python loops") -> Lesson:
        """Ensures minute invariants and required animation component on parsed lessons."""
        if weak_concept:
            durations = _distribute_minutes_adaptive(profile.minutes, len(lesson.sections) or 6)
        else:
            durations = _distribute_minutes(profile.minutes, len(lesson.sections) or 6)

        is_py = is_python_loops_topic(topic)

        for idx, sec in enumerate(lesson.sections):
            if idx < len(durations):
                sec.minutes = durations[idx]
            if sec.type == "example":
                if is_py and not sec.animation:
                    sec.animation = {"component": "range_viz", "start": 0, "end": 5}
                elif not is_py and not sec.animation:
                    sec.animation = {
                        "component": "step_viz",
                        "steps": [
                            {"title": f"Step 1: Introduction to {topic}", "detail": f"Understanding foundational elements of {topic}."},
                            {"title": "Step 2: Core Mechanism", "detail": f"Observing how core components of {topic} interact."},
                            {"title": "Step 3: Synthesis", "detail": f"Completing the operation and evaluating the result in {topic}."},
                        ],
                    }
            if sec.type == "quiz":
                sec.content = f"Next: a 5-question checkpoint on {topic}."

        lesson.total_minutes = profile.minutes
        lesson.weak_concept = weak_concept
        lesson.language = profile.language
        lesson.topic = topic
        return lesson

    def generate_quiz_llm(
        self,
        allowed_concept_ids: list[str],
        topic: str = "Python loops",
        concepts: Optional[list[dict[str, str]]] = None,
    ) -> Quiz:
        """
        Calls Gemini to generate a 5-question Quiz for topic.
        Questions must use only the allowed concept_ids.
        Each question: 1 correct answer, 4 options, concept_id from list,
        wrong options based on the concept's common_mistake.
        Rejects and retries if any rule is broken.
        """
        is_py = is_python_loops_topic(topic)

        allowed_list_str = ", ".join(f"'{cid}'" for cid in allowed_concept_ids)
        mistakes_list = []
        if concepts:
            for c in concepts:
                mistakes_list.append(f"- Concept '{c['concept_id']}': common mistake is '{c.get('common_mistake', '')}'")
        else:
            for cid in allowed_concept_ids:
                mistakes_list.append(f"- Concept '{cid}'")
        mistakes_block = "\n".join(mistakes_list)

        initial_prompt = f"""
You are an expert educational assessment designer.
Generate a 5-question multiple choice quiz on '{topic}'.
CRITICAL CONSTRAINTS:
1. Exactly 5 questions in the 'questions' array.
2. Quiz questions must use ONLY the allowed concept_ids: [{allowed_list_str}]. Do NOT use any other concept_id.
3. Each question must have exactly 4 options.
4. Exactly one correct answer specified by 0-based integer 'correct_index' (0, 1, 2, or 3).
5. Wrong options for each question MUST be based on the concept's common mistake:
{mistakes_block}
6. Each question must have a clear explanation.

Return a valid JSON object matching this schema:
{{
  "id": "quiz_generated",
  "topic": "{topic} Checkpoint",
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
            is_valid, reason = _validate_quiz_rules(quiz, allowed_concept_ids)
            if not is_valid:
                raise ValueError(reason)
            quiz.source = "Live AI"
            return quiz
        except Exception as first_error:
            sanitized_first = sanitize_error(f"{type(first_error).__name__}: {str(first_error)}")
            print(f"[LearnMate LOG] generate_quiz_llm initial attempt failed: {sanitized_first}", flush=True)
            # Reject and retry once if any rule is broken
            try:
                retry_prompt = (
                    f"{initial_prompt}\n\n"
                    f"Your previous response was rejected due to rule violation: {sanitized_first}.\n"
                    f"You must strictly fix this: exactly 5 questions, 4 options each, correct_index 0-3, and concept_id strictly from [{allowed_list_str}]."
                )
                raw_text_retry = self._call_gemini_raw(retry_prompt)
                data_retry = json.loads(raw_text_retry)
                quiz = Quiz.model_validate(data_retry)
                is_valid, reason = _validate_quiz_rules(quiz, allowed_concept_ids)
                if not is_valid:
                    raise ValueError(reason)
                quiz.source = "Live AI"
                return quiz
            except Exception as second_error:
                sanitized_second = sanitize_error(f"{type(second_error).__name__}: {str(second_error)}")
                print(f"[LearnMate LOG] generate_quiz_llm retry failed: {sanitized_second}", flush=True)
                if is_py:
                    return get_fallback_quiz(allowed_concept_ids)
                raise LiveAINeededError(
                    "Live AI is needed for this topic. Try Python loops.",
                    debug_details=f"{sanitized_second}\n(Initial attempt failed: {sanitized_first})",
                )


llm_service = LLMService()


def generate_concepts(topic: str, level: str = "beginner", goal: Optional[str] = None) -> list[dict[str, str]]:
    """Module-level function to generate 3 concepts {concept_id, name, common_mistake}."""
    return llm_service.generate_concepts(topic=topic, level=level, goal=goal)

