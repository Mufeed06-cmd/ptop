from __future__ import annotations

import streamlit as st
from schemas import Profile, Answer
from backend import generate_lesson, generate_quiz, submit_answers
from engine import engine


st.set_page_config(
    page_title="LearnMate - Python Loops Tutor",
    page_icon="🐍",
    layout="wide",
)


def render_range_viz(start: int = 0, end: int = 5):
    """
    Renders an interactive visual component for range_viz
    demonstrating start, stop bounds, and loop index progression.
    """
    st.markdown("#### 🔍 Interactive Visualizer: `range_viz`")
    st.info(f"Visualizing `range({start}, {end})` — Notice that start (`{start}`) is included, but stop (`{end}`) is **excluded**!")

    # Interactive step slider
    values = list(range(start, end))
    current_step = st.slider(
        "Step through loop iterations:",
        min_value=0,
        max_value=len(values) - 1,
        value=0,
        help="Slide to see which number the loop variable 'i' holds at each iteration."
    )

    cols = st.columns(end - start + 1)
    for idx, col in enumerate(cols):
        num = start + idx
        with col:
            if num < end:
                if idx == current_step:
                    st.markdown(
                        f"<div style='border: 3px solid #2ecc71; background-color: #d5f5e3; "
                        f"border-radius: 8px; text-align: center; padding: 12px; color: #1e8449;'>"
                        f"<div style='font-size: 20px; font-weight: bold;'>i = {num}</div>"
                        f"<span style='font-size: 12px; font-weight: bold;'>Active Step</span></div>",
                        unsafe_allow_html=True,
                    )
                elif idx < current_step:
                    st.markdown(
                        f"<div style='border: 1px solid #aed6f1; background-color: #ebf5fb; "
                        f"border-radius: 8px; text-align: center; padding: 12px; color: #2874a6;'>"
                        f"<div style='font-size: 20px;'>{num}</div>"
                        f"<span style='font-size: 11px;'>Visited</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='border: 1px solid #d5dbdb; background-color: #f8f9f9; "
                        f"border-radius: 8px; text-align: center; padding: 12px; color: #566573;'>"
                        f"<div style='font-size: 20px;'>{num}</div>"
                        f"<span style='font-size: 11px;'>Pending</span></div>",
                        unsafe_allow_html=True,
                    )
            else:
                # The stop bound (exclusive)
                st.markdown(
                    f"<div style='border: 2px dashed #e74c3c; background-color: #fadbd8; "
                    f"border-radius: 8px; text-align: center; padding: 12px; color: #922b21;'>"
                    f"<div style='font-size: 20px; font-weight: bold;'>{num}</div>"
                    f"<span style='font-size: 11px; font-weight: bold;'>Stop (Excluded)</span></div>",
                    unsafe_allow_html=True,
                )

    st.caption(f"Iteration **{current_step + 1} of {len(values)}**: `i = {values[current_step]}` | Loop executes body with `i`.")


# --- Sidebar: User Profile Setup ---
with st.sidebar:
    st.title("👤 Learner Profile")
    learner_name = st.text_input("Name", value="Alex")
    minutes_input = st.slider(
        "Available Time (Minutes)",
        min_value=6,
        max_value=60,
        value=15,
        step=1,
        help="Section durations will automatically sum strictly to this total.",
    )
    skill_level = st.selectbox("Skill Level", ["beginner", "intermediate", "advanced"], index=0)

    # Initialize / retrieve profile from engine
    profile = engine.get_or_create_profile(
        name=learner_name,
        minutes=minutes_input,
        skill_level=skill_level,
    )

    st.markdown("---")
    st.subheader("🎯 Targeted Focus")
    concept_options = ["None (General)", "range_bounds", "loop_body"]
    default_concept_idx = 0
    if profile.weak_concepts:
        st.warning(f"Detected Weak Areas: {', '.join(profile.weak_concepts)}")
        if profile.weak_concepts[0] in concept_options:
            default_concept_idx = concept_options.index(profile.weak_concepts[0])

    selected_concept = st.selectbox(
        "Focus on Weak Concept",
        concept_options,
        index=default_concept_idx,
    )
    active_weak_concept = None if selected_concept.startswith("None") else selected_concept

    st.markdown("---")
    st.caption("LearnMate Prototype (Mock Backend & Pydantic Engine)")


# --- Main Navigation Tabs ---
tab_lesson, tab_quiz, tab_progress = st.tabs(["📖 Lesson", "📝 Quiz", "📊 Progress & Results"])

# --- Tab 1: Lesson ---
with tab_lesson:
    st.header("Python Loops Masterclass")
    st.write(
        "Generate a tailored lesson chunked into 6 core sections summing exactly to your designated minutes."
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        generate_clicked = st.button("🚀 Generate Lesson", type="primary")

    if generate_clicked or "active_lesson" not in st.session_state:
        with st.spinner("Generating lesson..."):
            lesson = generate_lesson(profile, weak_concept=active_weak_concept)
            st.session_state["active_lesson"] = lesson

    active_lesson = st.session_state.get("active_lesson")

    if active_lesson:
        sum_minutes = sum(sec.minutes for sec in active_lesson.sections)
        st.success(
            f"**Topic:** {active_lesson.topic} | **Total Planned:** {active_lesson.total_minutes} mins "
            f"(Sections sum: **{sum_minutes} mins**)"
        )

        if active_lesson.weak_concept:
            st.info(f"Targeting remediation on: **{active_lesson.weak_concept}**")

        # Display the 6 sections
        section_icons = {
            "intro": "📘",
            "explain": "💡",
            "example": "🎨",
            "practice": "💻",
            "quiz": "❓",
            "recap": "🏁",
        }

        for sec in active_lesson.sections:
            icon = section_icons.get(sec.type, "📄")
            with st.expander(f"{icon} [{sec.type.upper()}] {sec.title} — {sec.minutes} min(s)", expanded=(sec.type in ["intro", "example"])):
                st.markdown(sec.content)

                if sec.code:
                    st.code(sec.code, language="python")

                # Handle animation component if present (e.g., example section)
                if sec.animation and sec.animation.get("component") == "range_viz":
                    render_range_viz(
                        start=sec.animation.get("start", 0),
                        end=sec.animation.get("end", 5),
                    )


# --- Tab 2: Quiz ---
with tab_quiz:
    st.header("Loops Checkpoint Quiz")
    st.write("Answer 5 questions testing your grasp on `range_bounds` and `loop_body` mechanics.")

    if "active_quiz" not in st.session_state:
        st.session_state["active_quiz"] = generate_quiz(concept_ids=["range_bounds", "loop_body"])

    current_quiz = st.session_state["active_quiz"]

    with st.form("quiz_form"):
        submitted_answers: dict[str, str] = {}
        for idx, q in enumerate(current_quiz.questions, start=1):
            st.markdown(f"**Question {idx}:** {q.question}")
            st.caption(f"Concept: `{q.concept_id}`")
            choice = st.radio(
                f"Select an answer for Question {idx}:",
                options=q.options,
                key=f"quiz_opt_{q.id}",
                index=0,
            )
            submitted_answers[q.id] = choice
            st.markdown("---")

        submit_btn = st.form_submit_button("Submit Quiz Answers", type="primary")

    if submit_btn:
        answer_objects = [
            Answer(question_id=qid, selected_answer=ans)
            for qid, ans in submitted_answers.items()
        ]
        result = submit_answers(answer_objects)
        st.session_state["quiz_result"] = result
        # Update engine
        engine.evaluate_quiz(answer_objects, profile=profile)
        st.success(f"Quiz submitted! Score: {result.score}/{result.total} ({result.percentage}%)")


# --- Tab 3: Progress & Results ---
with tab_progress:
    st.header("Assessment & Diagnostic Results")
    latest_result = st.session_state.get("quiz_result")

    if not latest_result:
        st.info("Complete the quiz in the 'Quiz' tab to view your score breakdown and diagnostic insights.")
    else:
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Score", f"{latest_result.score} / {latest_result.total}")
        with metric_col2:
            st.metric("Percentage", f"{latest_result.percentage}%")
        with metric_col3:
            st.metric("Status", "Passed ✅" if latest_result.passed else "Needs Review ⚠️")

        st.markdown(f"**Feedback:** {latest_result.feedback}")

        if latest_result.weak_concepts:
            st.error(f"⚠️ Concepts flagged for improvement: **{', '.join(latest_result.weak_concepts)}**")
            for wc in latest_result.weak_concepts:
                if st.button(f"Generate targeted lesson for '{wc}'", key=f"btn_remedy_{wc}"):
                    st.session_state["active_lesson"] = generate_lesson(profile, weak_concept=wc)
                    st.success(f"Generated new lesson focusing on {wc}! Check the 'Lesson' tab.")
        else:
            st.balloons()
            st.success("No weak concepts detected! You scored 100% on the core loop concepts.")

        st.subheader("Question Breakdown")
        for detail in latest_result.details:
            icon = "✅" if detail["is_correct"] else "❌"
            with st.expander(f"{icon} {detail['question'][:60]}..."):
                st.markdown(f"**Question:** {detail['question']}")
                st.markdown(f"- **Your Answer:** {detail['selected_answer']}")
                st.markdown(f"- **Correct Answer:** {detail['correct_answer']}")
                st.markdown(f"- **Concept ID:** `{detail['concept_id']}`")
                st.markdown(f"- **Explanation:** {detail['explanation']}")
