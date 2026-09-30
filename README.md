# LearnMate 🐍

LearnMate is an adaptive Python learning assistant that generates time-boxed lessons, interactive concept visualizations, and diagnostic checkpoint quizzes.

## Project Structure

```
learnmate/
├── app.py              # Streamlit web interface with interactive range visualizer
├── backend.py          # Mock lesson & quiz generation, and answer evaluation
├── schemas.py          # Pydantic models (Profile, Lesson, Quiz, Answer, Result, etc.)
├── db.py               # Local JSON-backed session and history database
├── llm.py              # Gemini client stub with fallback to mock responses
├── engine.py           # Pedagogical engine orchestrating profile, lessons, & diagnostics
├── requirements.txt    # Project dependencies (streamlit, pydantic, google-generativeai)
└── test_learnmate.py   # Unit test suite verifying mock data & Pydantic models
```

## Features

- **Time-Boxed Lessons**: The 6 lesson sections (`intro`, `explain`, `example`, `practice`, `quiz`, `recap`) strictly sum to `profile.minutes`.
- **Interactive Visualizer**: The `example` section includes an interactive `range_viz` component (`{"component": "range_viz", "start": 0, "end": 5}`) to visualize lower and upper loop bounds.
- **Diagnostic Quizzes**: 5 questions covering `range_bounds` and `loop_body`. Mistaken questions automatically flag weak concepts and recommend remedial focus.
- **Pluggable Gemini Integration**: Ready for Gemini API keys via `llm.py` without breaking offline or mocked execution.

## Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python3 -m unittest test_learnmate.py
```

### 3. Launch Streamlit Application
```bash
streamlit run app.py
```
