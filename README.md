# LearnMate 🐍

LearnMate is an adaptive Python learning assistant that dynamically generates time-boxed lessons, interactive concept visualizations, and diagnostic checkpoint quizzes powered by Google Gemini and SQLite mastery tracking.

## Architecture & Modules

```
learnmate/
├── app.py              # Streamlit web interface with visual range stepper & mastery dashboard
├── backend.py          # Real orchestration layer wiring LLM service, SQLite, and adaptive engine
├── db.py               # SQLite storage: sessions, questions, attempts, mastery(concept_id, score DEFAULT 0.5)
├── engine.py           # Evaluates against correct_index, updates mastery EMA, detects weak_concept & next_focus
├── llm.py              # Gemini client (JSON mode, temperature 0.3, 1-retry on invalid schema, fallback)
├── schemas.py          # Pydantic models (Profile, LessonSection, Lesson, Question, Quiz, Answer, Result)
├── requirements.txt    # Project dependencies (streamlit, pydantic, google-generativeai)
└── test_learnmate.py   # Automated unit tests covering mastery math, DB, LLM retries, and invariants
```

## Key Mechanisms

### 1. SQLite Storage (`db.py`)
- **`sessions`**: `id`, `user_id`, `topic`, `created_at`
- **`questions`**: `id`, `concept_id`, `question`, `options`, `correct_index`, `explanation`, `session_id`, `created_at`
- **`attempts`**: `id`, `session_id`, `question_id`, `selected_index`, `outcome`, `timestamp`
- **`mastery`**: `concept_id`, `score` (default `0.5`)

### 2. Adaptive Learning Engine (`engine.py`)
- **Scoring**: Evaluates each student answer against `question.correct_index`.
- **Mastery Update Formula**:
  $$\text{mastery} \leftarrow \text{mastery} + 0.3 \times (\text{outcome} - \text{mastery})$$
  *(Where $\text{outcome} = 1.0$ for correct, $0.0$ for incorrect).*
- **Weak Concept Identification**: Concept with the lowest mastery score strictly below `0.6` (or `None` if all $\ge 0.6$).
- **Next Focus**: A concise one-line string explaining what the next lesson will target.

### 3. Gemini LLM Integration (`llm.py`)
- Reads API key strictly from the `GEMINI_API_KEY` environment variable. Never hardcoded.
- Uses `temperature: 0.3` and `response_mime_type: "application/json"`.
- Validates structured JSON into Pydantic models.
- **Robust Error Handling**: If validation fails, retries once providing the specific error message to Gemini. If it fails again (or if offline / unconfigured), automatically serves a structured fallback lesson/quiz.
- **Prompt Constraints**:
  - Lessons: Includes `"Explain in {language}. Keep code and technical terms in English."` and, if `weak_concept` is set, `"The student struggled with {weak_concept}. Use a step-by-step trace explanation and address the common mistake."`
  - Quizzes: Strictly constrained to use only the allowed `concept_ids`.

## Quick Start

### 1. Set Your Gemini API Key
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Unit Tests
```bash
python3 -m unittest test_learnmate.py
```

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
