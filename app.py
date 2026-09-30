from __future__ import annotations

import os
import textwrap
import streamlit as st
from schemas import Profile, Answer
from backend import generate_lesson, generate_quiz, submit_answers
from animations import render_animation
import styles
import db

# Page Configuration
st.set_page_config(
    page_title="LearnMate AI | Adaptive Loops Mentor",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Apply Teammates' SaaS Styling (flush-left)
st.markdown(textwrap.dedent(styles.CUSTOM_CSS), unsafe_allow_html=True)


# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------
def set_step(new_step: str) -> None:
    """Updates session state flow step and triggers immediate UI refresh."""
    st.session_state["step"] = new_step
    st.rerun()


def reset_demo() -> None:
    """Deletes SQLite DB records/file and clears all Streamlit session state."""
    try:
        db.reset_db()
        if db.DB_PATH.exists():
            os.remove(db.DB_PATH)
    except Exception:
        pass
    db.init_db()
    st.session_state.clear()
    st.rerun()


# ----------------------------------------------------
# Session State Initialization
# ----------------------------------------------------
if "step" not in st.session_state:
    st.session_state["step"] = "landing"

if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = Profile(
        name="",
        minutes=15,
        language="English",
        skill_level="beginner",
    )

if "lesson" not in st.session_state:
    st.session_state["lesson"] = None

if "quiz" not in st.session_state:
    st.session_state["quiz"] = None

if "result" not in st.session_state:
    st.session_state["result"] = None

if "quiz_attempt" not in st.session_state:
    st.session_state["quiz_attempt"] = 1

if "is_adaptive" not in st.session_state:
    st.session_state["is_adaptive"] = False


# ====================================================
# SCREEN 0: LANDING SCREEN
# ====================================================
def render_landing_screen():
    st.markdown(styles.render_header(), unsafe_allow_html=True)

    st.markdown(
        textwrap.dedent(
            """
            <div style="text-align: center; padding: 24px 0 16px 0;">
                <h1 style="font-size: 38px; font-weight: 800; background: linear-gradient(135deg, #a5b4fc 0%, #38bdf8 50%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;">
                    ✦ LearnMate AI
                </h1>
                <p style="font-size: 17.5px; color: #cbd5e1; max-width: 780px; margin: 0 auto 28px auto; line-height: 1.6;">
                    LearnMate teaches you within your available time, measures what you don't understand, and changes the next lesson to fix it.
                </p>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown(
            textwrap.dedent(
                """
                <div class="lm-card" style="height: 100%; border-color: rgba(56, 189, 248, 0.3);">
                    <div style="font-size: 26px; margin-bottom: 10px;">⏱️</div>
                    <h3 style="color: #38bdf8; margin: 0 0 8px 0; font-size: 18px;">Time-Boxed Lessons</h3>
                    <p style="color: #94a3b8; font-size: 13.5px; line-height: 1.6; margin: 0;">
                        Specify your available minutes (6 to 60 min). Every section is automatically portioned to guarantee you finish strictly within your schedule.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            textwrap.dedent(
                """
                <div class="lm-card" style="height: 100%; border-color: rgba(129, 140, 248, 0.3);">
                    <div style="font-size: 26px; margin-bottom: 10px;">🧠</div>
                    <h3 style="color: #818cf8; margin: 0 0 8px 0; font-size: 18px;">Adaptive to Your Mistakes</h3>
                    <p style="color: #94a3b8; font-size: 13.5px; line-height: 1.6; margin: 0;">
                        Targeted quizzes evaluate cognitive blind spots. If concept mastery falls below 0.6, your next lesson reconstructs the mental model with execution traces.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            textwrap.dedent(
                """
                <div class="lm-card" style="height: 100%; border-color: rgba(16, 185, 129, 0.3);">
                    <div style="font-size: 26px; margin-bottom: 10px;">🗣️</div>
                    <h3 style="color: #34d399; margin: 0 0 8px 0; font-size: 18px;">English / Telugu / Hindi</h3>
                    <p style="color: #94a3b8; font-size: 13.5px; line-height: 1.6; margin: 0;">
                        Multilingual mentoring with authentic regional vernacular concept cues while keeping Python code syntax and industry terms in English.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    st.write("")
    st.write("")
    col_btn_left, col_btn_center, col_btn_right = st.columns([1, 1.2, 1])
    with col_btn_center:
        if st.button("Start Learning 🚀", type="primary", use_container_width=True, key="btn_start_learning_landing"):
            set_step("form")


# ====================================================
# SCREEN 1: SETUP FORM
# ====================================================
def render_form_screen():
    profile: Profile = st.session_state["user_profile"]

    st.markdown(styles.render_header(profile), unsafe_allow_html=True)
    st.markdown(styles.render_stepper(1), unsafe_allow_html=True)

    col_left, col_right = st.columns([1.15, 0.85], gap="large")

    with col_left:
        st.markdown(
            textwrap.dedent(
                """
                <div class="lm-card lm-card-highlight">
                    <h3 style="margin-top:0; color:#38bdf8; font-size: 20px;">🎯 Configure Your Micro-Sprint</h3>
                    <p style="color:#94a3b8; font-size: 13.5px; margin-bottom: 4px;">
                        LearnMate AI adapts to your exact available time budget, diagnoses concepts you struggle with, 
                        and personalizes the next lesson to cure your blind spots.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        # Quick-pick chips
        st.markdown("<p style='font-weight:600; color:#cbd5e1; margin-bottom:6px;'>Quick-pick topic:</p>", unsafe_allow_html=True)
        chips = ["Python loops", "SQL joins", "Photosynthesis", "World War 2"]
        chip_cols = st.columns(4)
        for col, chip_text in zip(chip_cols, chips):
            if col.button(chip_text, key=f"chip_btn_{chip_text}", use_container_width=True):
                st.session_state["topic_input"] = chip_text
                st.rerun()

        current_topic_val = st.session_state.get("topic_input", profile.topic or "Python loops")

        with st.form("learning_setup_form"):
            st.markdown("<p style='font-weight:600; color:#cbd5e1; margin-bottom:4px;'>Learner Name (Optional)</p>", unsafe_allow_html=True)
            learner_name = st.text_input(
                "Learner Name",
                value=profile.name if profile.name else "",
                placeholder="Optional (e.g. Learner)",
                key="form_name_input",
                label_visibility="collapsed",
            )

            st.markdown("<p style='font-weight:600; color:#cbd5e1; margin-bottom:4px; margin-top:14px;'>What do you want to learn?</p>", unsafe_allow_html=True)
            topic_input = st.text_input(
                "What do you want to learn?",
                value=current_topic_val,
                placeholder="e.g. Python loops, SQL joins, Photosynthesis, World War 2",
                key="form_topic_input",
                label_visibility="collapsed",
            )

            st.markdown("<p style='font-weight:600; color:#cbd5e1; margin-bottom:4px; margin-top:14px;'>Current Experience Level</p>", unsafe_allow_html=True)
            level_options = ["beginner", "intermediate", "advanced"]
            current_level_idx = level_options.index(profile.skill_level) if profile.skill_level in level_options else 0
            skill_level = st.selectbox(
                "Level",
                level_options,
                index=current_level_idx,
                key="form_level_select",
                label_visibility="collapsed",
            )

            st.markdown("<p style='font-weight:600; color:#cbd5e1; margin-bottom:4px; margin-top:14px;'>Instruction Language</p>", unsafe_allow_html=True)
            lang_options = ["English", "English + Telugu", "English + Hindi"]
            current_lang_idx = lang_options.index(profile.language) if profile.language in lang_options else 0
            language = st.selectbox(
                "Language",
                lang_options,
                index=current_lang_idx,
                key="form_lang_select",
                label_visibility="collapsed",
            )

            st.markdown("<p style='font-weight:600; color:#cbd5e1; margin-bottom:4px; margin-top:14px;'>Available Time Budget (Minutes)</p>", unsafe_allow_html=True)
            time_budget = st.slider(
                "Time Budget",
                min_value=6,
                max_value=60,
                value=int(profile.minutes) if profile.minutes >= 6 else 15,
                step=1,
                key="form_time_slider",
                label_visibility="collapsed",
                help="Section durations will automatically sum strictly to this total.",
            )

            st.write("")
            submit_form = st.form_submit_button(
                "Launch My Personalized Lesson 🚀",
                type="primary",
            )

            if submit_form:
                selected_topic = topic_input.strip() if topic_input and topic_input.strip() else "Python loops"
                st.session_state["topic_input"] = selected_topic

                new_profile = Profile(
                    name=learner_name.strip(),
                    minutes=time_budget,
                    language=language,
                    skill_level=skill_level,
                    topic=selected_topic,
                )
                st.session_state["user_profile"] = new_profile

                try:
                    with st.spinner(f"Synthesizing tailored lesson & checkpoint for '{selected_topic}'..."):
                        from llm import generate_concepts, LiveAINeededError, is_python_loops_topic
                        concepts = generate_concepts(selected_topic, level=skill_level)
                        concept_ids = [c["concept_id"] for c in concepts]
                        lesson = generate_lesson(new_profile)
                        quiz = generate_quiz(concept_ids=concept_ids, topic=selected_topic, concepts=concepts)
                        st.session_state["lesson"] = lesson
                        st.session_state["quiz"] = quiz
                        st.session_state["is_adaptive"] = False
                        st.session_state["quiz_attempt"] = 1
                    set_step("lesson")
                except LiveAINeededError:
                    st.error("Live AI is needed for this topic. Try Python loops.")
                except Exception as e:
                    from llm import is_python_loops_topic
                    if not is_python_loops_topic(selected_topic):
                        st.error("Live AI is needed for this topic. Try Python loops.")
                    else:
                        st.error(f"Error generating lesson: {e}")

    with col_right:
        st.markdown(
            textwrap.dedent(
                """
                <div class="lm-card">
                    <h4 style="color:#a5b4fc; margin-top:0;">⚡ The Closed-Loop Adaptive Engine</h4>
                    <div style="font-size: 13.5px; color:#cbd5e1; line-height: 1.8;">
                        <div style="margin-bottom: 12px; display:flex; gap:10px;">
                            <span style="color:#38bdf8; font-weight:bold;">1. Time Budgeting:</span>
                            <span>All 6 sections strictly portioned to fit your designated time budget.</span>
                        </div>
                        <div style="margin-bottom: 12px; display:flex; gap:10px;">
                            <span style="color:#38bdf8; font-weight:bold;">2. Interactive Visuals:</span>
                            <span>Embedded simulator reveals range boundaries and control flow.</span>
                        </div>
                        <div style="margin-bottom: 12px; display:flex; gap:10px;">
                            <span style="color:#38bdf8; font-weight:bold;">3. Checkpoint Quiz:</span>
                            <span>Targeted questions uncover cognitive blind spots.</span>
                        </div>
                        <div style="display:flex; gap:10px;">
                            <span style="color:#38bdf8; font-weight:bold;">4. Adaptive Cure:</span>
                            <span>AI diagnoses weak concepts below 0.6 and restructures the next lesson.</span>
                        </div>
                    </div>
                </div>

                <div class="lm-card" style="border-color: rgba(56, 189, 248, 0.25);">
                    <h4 style="color:#38bdf8; margin-top:0;">💡 Multilingual Mentorship</h4>
                    <p style="font-size: 13px; color:#94a3b8; margin:0; line-height: 1.6;">
                        Need vernacular clarity? Select <b>English + Telugu</b> or <b>English + Hindi</b> 
                        to receive authentic regional concept explanations while keeping Python code in English.
                    </p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        cur_topic_for_mastery = st.session_state.get("topic_input", profile.topic or "Python loops")
        mastery_map = db.get_all_mastery(topic=cur_topic_for_mastery)
        if mastery_map:
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="lm-card">
                        <h4 style="color:#fcd34d; margin-top:0;">📊 Current Concept Mastery ({cur_topic_for_mastery})</h4>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            for cid, score in mastery_map.items():
                st.write(f"**{cid}**: `{score:.2f}`")
                st.progress(min(1.0, max(0.0, score)))

        st.write("")
        if st.button("🗑️ Reset Demo (Clear SQLite DB & Session)", key="btn_reset_demo_form"):
            reset_demo()


# ====================================================
# SCREEN 2: LESSON (STANDARD OR ADAPTIVE)
# ====================================================
def render_lesson_screen():
    profile: Profile = st.session_state["user_profile"]
    lesson = st.session_state.get("lesson")
    is_adaptive = st.session_state.get("is_adaptive", False)
    result = st.session_state.get("result")

    if not lesson:
        set_step("form")
        return

    st.markdown(styles.render_header(profile), unsafe_allow_html=True)
    st.markdown(styles.render_stepper(2), unsafe_allow_html=True)

    # What Changed Banner & "Your Mistake" Box on Adaptive / Weak Concept Lesson
    if (is_adaptive or lesson.weak_concept):
        if result and result.next_focus:
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="lm-card" style="border: 2px solid #818cf8; background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(15, 23, 42, 0.9) 100%); margin-bottom: 20px;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 6px;">
                            <span style="font-size: 20px;">🧠</span>
                            <h3 style="margin:0; color:#a5b4fc; font-size:18px;">What Changed: Adaptive Remedial Focus</h3>
                        </div>
                        <p style="color:#f8fafc; font-size:14px; margin-bottom:0; line-height:1.6;">
                            {result.next_focus}
                        </p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        # "Your Mistake" Box showing what the user got wrong and why
        rendered_mistake = False
        if result and result.details:
            wrong_items = [d for d in result.details if not d.get("is_correct")]
            if wrong_items:
                rendered_mistake = True
                for w in wrong_items:
                    st.markdown(
                        textwrap.dedent(
                            f"""
                            <div class="lm-card lm-card-danger" style="margin-bottom: 16px;">
                                <div class="lm-weak-pulse" style="margin-bottom: 6px;">
                                    <span>⚠️</span> Your Mistake in the Checkpoint Quiz
                                </div>
                                <h4 style="color: #f87171; margin-top: 4px; margin-bottom: 8px;">{w['question']}</h4>
                                <p style="color: #cbd5e1; font-size: 13.5px; margin-bottom: 4px;">
                                    <b>Your Selected Option:</b> <code style="color:#f87171;">{w['selected_answer']}</code> (Index {w['selected_index']})
                                </p>
                                <p style="color: #cbd5e1; font-size: 13.5px; margin-bottom: 6px;">
                                    <b>Correct Answer:</b> <code style="color:#34d399;">{w['correct_answer']}</code> (Index {w['correct_index']})
                                </p>
                                <p style="color: #38bdf8; font-size: 13px; margin-bottom: 0;">
                                    💡 <b>Why this was wrong:</b> {w['explanation']}
                                </p>
                            </div>
                            """
                        ),
                        unsafe_allow_html=True,
                    )
        if not rendered_mistake and lesson.weak_concept:
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="lm-card lm-card-danger" style="margin-bottom: 16px;">
                        <div class="lm-weak-pulse" style="margin-bottom: 6px;">
                            <span>⚠️</span> Your Mistake / Weak Concept Remediation
                        </div>
                        <h4 style="color: #f87171; margin-top: 4px; margin-bottom: 8px;">Focus Concept: <code>{lesson.weak_concept}</code></h4>
                        <p style="color: #cbd5e1; font-size: 13.5px; margin-bottom: 6px;">
                            The adaptive engine diagnosed low concept mastery on <b>{lesson.weak_concept}</b>.
                        </p>
                        <p style="color: #38bdf8; font-size: 13px; margin-bottom: 0;">
                            💡 <b>Pedagogical Adjustment:</b> This remedial lesson breaks down <code>{lesson.weak_concept}</code> step-by-step using an alternative pedagogical method (analogy, execution trace, and visual stepper) to resolve misconceptions.
                        </p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    # Lesson Overview Banner (clean, flush-left HTML without stray tags)
    sum_minutes = sum(sec.minutes for sec in lesson.sections)
    adaptive_tag = (
        '<span class="lm-badge" style="background:rgba(239, 68, 68, 0.2); color:#fca5a5;">🧠 Adaptive Remedial Sprint</span>'
        if is_adaptive
        else '<span class="lm-badge" style="background:rgba(56, 189, 248, 0.2); color:#38bdf8;">📖 Standard Sprint</span>'
    )
    badge_label = getattr(lesson, "source", None) or "Live AI"
    badge_styles = {
        "Live AI": "background:rgba(16, 185, 129, 0.2); color:#34d399; border: 1px solid rgba(16, 185, 129, 0.5);",
        "Cached": "background:rgba(56, 189, 248, 0.2); color:#38bdf8; border: 1px solid rgba(56, 189, 248, 0.5);",
        "Fallback": "background:rgba(245, 158, 11, 0.2); color:#fbbf24; border: 1px solid rgba(245, 158, 11, 0.5);",
    }
    badge_style = badge_styles.get(badge_label, badge_styles["Live AI"])
    badge_tag = f'<span class="lm-badge" style="{badge_style}">⚡ {badge_label}</span>'
    focus_text = f" | Focus Area: <b>{lesson.weak_concept}</b>" if lesson.weak_concept else ""

    st.markdown(
        textwrap.dedent(
            f"""
            <div class="lm-card lm-card-highlight">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div style="display:flex; gap:8px; align-items:center;">
                        {adaptive_tag}
                        {badge_tag}
                    </div>
                    <span class="lm-badge lm-badge-timer">⏱️ Total: {lesson.total_minutes} min Budget ({len(lesson.sections)} sections sum: {sum_minutes} min)</span>
                </div>
                <h2 style="color: #ffffff; margin-top: 0; font-size: 24px;">{lesson.topic}</h2>
                <div style="color: #cbd5e1; font-size: 14.5px; line-height: 1.6;">
                    Language: <b>{lesson.language}</b> | Skill Level: <b>{profile.skill_level.capitalize()}</b>{focus_text}
                </div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # Render All 6 Lesson Sections with st.markdown inside containers
    section_icons = {
        "intro": "📘",
        "explain": "💡",
        "example": "🎨",
        "practice": "💻",
        "quiz": "❓",
        "recap": "🏁",
    }

    for i, sec in enumerate(lesson.sections):
        icon = section_icons.get(sec.type, "📄")
        with st.container():
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px 12px 0 0; padding: 12px 18px; margin-top: 18px; display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: #38bdf8; font-size: 17px;">{icon} [{sec.type.upper()}] {sec.title}</h3>
                        <span class="lm-badge lm-badge-timer">⏱️ {sec.minutes} min</span>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                st.markdown(sec.content)

                if sec.code:
                    st.markdown("<p style='font-size: 12px; font-weight: 700; color: #a5b4fc; margin-bottom: 2px;'>💻 Code Syntax:</p>", unsafe_allow_html=True)
                    st.code(sec.code, language="python")

                if sec.animation:
                    st.markdown("<p style='font-size: 12px; font-weight: 700; color: #38bdf8; margin-top: 10px; margin-bottom: 4px;'>⚙️ Interactive Execution Simulator:</p>", unsafe_allow_html=True)
                    render_animation(sec.animation)

    # Navigation Footer to Quiz
    btn_label = "Proceed to Adaptive Checkpoint Quiz ⚡" if is_adaptive else "Proceed to Checkpoint Quiz ⚡"
    btn_key = "btn_proceed_quiz_adaptive" if is_adaptive else "btn_proceed_quiz_std"

    st.write("")
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button(btn_label, key=btn_key, type="primary"):
            set_step("quiz")
    with col_nav2:
        if st.button("⬅️ Adjust Setup / Time Budget", key=f"btn_back_form_{is_adaptive}"):
            set_step("form")


# ====================================================
# SCREEN 3: CHECKPOINT QUIZ
# ====================================================
def render_quiz_screen():
    profile: Profile = st.session_state["user_profile"]
    quiz = st.session_state.get("quiz")
    attempt = st.session_state.get("quiz_attempt", 1)

    if not quiz or not quiz.questions:
        set_step("form")
        return

    st.markdown(styles.render_header(profile), unsafe_allow_html=True)
    st.markdown(styles.render_stepper(3), unsafe_allow_html=True)

    st.markdown(
        textwrap.dedent(
            f"""
            <div class="lm-card lm-card-highlight">
                <h3 style="margin-top:0; color:#38bdf8; font-size: 20px;">⚡ {quiz.topic}</h3>
                <p style="color:#94a3b8; font-size: 13.5px; margin-bottom: 0;">
                    Answer the {len(quiz.questions)} questions below. The diagnostic engine evaluates your answers against 
                    <code>correct_index</code>, updates SQLite concept mastery, and diagnoses any misconceptions.
                </p>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    with st.form("checkpoint_quiz_form"):
        submitted_choices: dict[str, int] = {}

        for i, q in enumerate(quiz.questions):
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div style="margin-top: 18px; margin-bottom: 8px;">
                        <span class="lm-badge" style="background:rgba(56, 189, 248, 0.15); color:#38bdf8;">Question {i + 1} of {len(quiz.questions)}</span>
                        <span style="font-size: 12px; color: #94a3b8; margin-left: 8px;">Concept ID: <code>{q.concept_id}</code></span>
                        <h4 style="color: #f8fafc; font-size: 15px; margin-top: 8px; margin-bottom: 10px;">{q.question}</h4>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            radio_key = f"quiz_q_{q.id}_attempt_{attempt}"
            selected_option = st.radio(
                label=f"Options for {q.id}",
                options=q.options,
                index=0,
                key=radio_key,
                label_visibility="collapsed",
            )
            submitted_choices[q.id] = q.options.index(selected_option) if selected_option in q.options else 0

            if i < len(quiz.questions) - 1:
                st.markdown("<hr style='border:0; border-top: 1px solid rgba(255,255,255,0.06); margin: 20px 0;'>", unsafe_allow_html=True)

        st.write("")
        submit_btn = st.form_submit_button(
            "Submit Answers & Diagnose Weak Concepts 🧠",
            type="primary",
            key=f"btn_submit_quiz_{attempt}",
        )

        if submit_btn:
            answers = [
                Answer(question_id=qid, selected_index=idx)
                for qid, idx in submitted_choices.items()
            ]
            active_topic = quiz.topic if quiz else (profile.topic or "Python loops")
            with st.spinner("Scoring against correct_index & updating SQLite mastery EMA..."):
                result = submit_answers(answers, topic=active_topic)
                st.session_state["result"] = result
            set_step("feedback")


# ====================================================
# SCREEN 4: FEEDBACK & ADAPTIVE DIAGNOSIS
# ====================================================
def render_feedback_screen():
    profile: Profile = st.session_state["user_profile"]
    result = st.session_state.get("result")

    if not result:
        set_step("form")
        return

    st.markdown(styles.render_header(profile), unsafe_allow_html=True)
    st.markdown(styles.render_stepper(4), unsafe_allow_html=True)

    # Top Row: Score Display & Weak Concept Alert
    col_score, col_alert = st.columns([0.8, 1.2], gap="large")

    with col_score:
        score_pct = int(result.percentage)
        score_color = "#10b981" if score_pct >= 80 else ("#f59e0b" if score_pct >= 50 else "#ef4444")
        st.markdown(
            textwrap.dedent(
                f"""
                <div class="lm-card" style="text-align: center; border-color: {score_color}55;">
                    <div class="lm-score-circle" style="border-color: {score_color}; box-shadow: 0 0 25px {score_color}44;">
                        <div class="lm-score-val" style="color: {score_color};">{score_pct}%</div>
                        <div class="lm-score-label">{result.score} of {result.total} Correct</div>
                    </div>
                    <h4 style="margin: 0; color: #f8fafc;">Diagnostic Performance</h4>
                    <p style="color: #94a3b8; font-size: 13px; margin-top: 6px;">{result.feedback}</p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    with col_alert:
        if result.weak_concept:
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="lm-card lm-card-danger">
                        <div class="lm-weak-pulse">
                            <span>⚠️</span> Weak Concept Diagnosed (&lt; 0.6)
                        </div>
                        <h3 style="color: #f87171; margin-top: 14px; font-size: 20px;">{result.weak_concept}</h3>
                        <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 0;">
                            The SQLite adaptive engine detected low mastery on <b>{result.weak_concept}</b>. 
                            Rather than forcing you to repeat the entire course, LearnMate creates a targeted 
                            adaptive lesson below with step-by-step trace explanations!
                        </p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
        else:
            st.balloons()
            st.markdown(
                textwrap.dedent(
                    """
                    <div class="lm-card lm-card-success">
                        <div class="lm-badge" style="background: rgba(16, 185, 129, 0.2); color:#34d399;">
                            <span>🏆</span> Full Concept Mastery
                        </div>
                        <h3 style="color: #34d399; margin-top: 14px; font-size: 20px;">All Loop Concepts Mastered (≥ 0.6)!</h3>
                        <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 0;">
                            You scored high across all tested concepts. Your next adaptive sprint will guide 
                            you to advanced iteration patterns and optimization techniques.
                        </p>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    # Concept Mastery Breakdown (SQLite EMA)
    st.markdown(
        textwrap.dedent(
            """
            <div style="margin-top: 18px; margin-bottom: 12px;">
                <h4 style="color:#a5b4fc; margin-bottom: 4px;">📊 Concept Mastery Breakdown (SQLite EMA)</h4>
                <span style="font-size: 12.5px; color: #94a3b8;">Updated via: <code>mastery += 0.3 * (outcome - mastery)</code></span>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    for concept, mastery in result.mastery_scores.items():
        pct = int(mastery * 100)
        col_cname, col_cpct = st.columns([1.6, 0.4])
        with col_cname:
            st.markdown(f"<span style='font-size: 14px; font-weight: 600; color: #e2e8f0;'>{concept}</span>", unsafe_allow_html=True)
        with col_cpct:
            color = "#10b981" if pct >= 60 else "#ef4444"
            st.markdown(f"<span style='font-size: 14px; font-weight: 700; color: {color}; float: right;'>{mastery:.2f} ({pct}%)</span>", unsafe_allow_html=True)
        st.progress(float(min(1.0, max(0.0, mastery))))

    # Next Lesson Focus Box
    st.markdown("<hr style='border:0; border-top: 1px solid rgba(255,255,255,0.08); margin: 24px 0;'>", unsafe_allow_html=True)
    st.markdown(
        textwrap.dedent(
            f"""
            <div class="lm-card" style="border: 2px solid #6366f1; background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(30, 41, 59, 0.6) 100%); padding: 22px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <span style="font-size: 22px;">🎯</span>
                    <h3 style="margin: 0; color: #a5b4fc; font-size: 18px;">Next lesson focuses on...</h3>
                </div>
                <p style="font-size: 14.5px; color: #f1f5f9; line-height: 1.6; margin-bottom: 0;">
                    {result.next_focus}
                </p>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    # Action Buttons: Start Adaptive Lesson, Reset Form
    col_adapt_btn, col_reset_btn = st.columns([1.2, 0.8])
    with col_adapt_btn:
        if st.button("🚀 Start Adaptive Lesson", key="btn_start_adaptive_lesson", type="primary"):
            active_topic = profile.topic or (st.session_state.get("lesson").topic if st.session_state.get("lesson") else "Python loops")
            with st.spinner("Generating adaptive remedial lesson tailored to diagnosed weak concept..."):
                adaptive_lesson = generate_lesson(profile, weak_concept=result.weak_concept)
                quiz_concepts = [result.weak_concept] if result.weak_concept else (st.session_state.get("quiz").concept_ids if st.session_state.get("quiz") else ["range_bounds", "loop_body"])
                adaptive_quiz = generate_quiz(concept_ids=quiz_concepts, topic=active_topic)
                st.session_state["lesson"] = adaptive_lesson
                st.session_state["quiz"] = adaptive_quiz
                st.session_state["is_adaptive"] = True
                st.session_state["quiz_attempt"] = st.session_state.get("quiz_attempt", 1) + 1
            set_step("adaptive_lesson")

    with col_reset_btn:
        if st.button("🔄 Start New Topic / Reset Form", key="btn_feedback_reset"):
            set_step("form")

    # Detailed Question-by-Question Review Expander
    with st.expander("🔍 View Question-by-Question Breakdown & Explanations"):
        for item in result.details:
            status_icon = "✅" if item["is_correct"] else "❌"
            status_color = "#34d399" if item["is_correct"] else "#f87171"
            st.markdown(
                textwrap.dedent(
                    f"""
                    <div style="background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                        <div style="font-weight: 700; color: {status_color}; margin-bottom: 6px;">
                            {status_icon} {item['question']}
                        </div>
                        <div style="font-size: 13px; color: #cbd5e1; margin-bottom: 4px;">
                            <b>Concept ID:</b> <code>{item['concept_id']}</code>
                        </div>
                        <div style="font-size: 13px; color: #94a3b8; margin-bottom: 6px;">
                            <b>Your Choice (Index {item['selected_index']}):</b> {item['selected_answer']} | 
                            <b>Correct (Index {item['correct_index']}):</b> {item['correct_answer']}
                        </div>
                        <div style="font-size: 12.5px; color: #38bdf8;">
                            💡 <b>Explanation:</b> {item['explanation']}
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

    st.write("")
    if st.button("🗑️ Reset Demo (Clear SQLite DB & Session)", key="btn_reset_demo_feedback"):
        reset_demo()


# ====================================================
# MAIN DISPATCHER
# ====================================================
current_step = st.session_state.get("step", "landing")

if current_step == "landing":
    render_landing_screen()
elif current_step == "form":
    render_form_screen()
elif current_step == "lesson":
    render_lesson_screen()
elif current_step == "quiz":
    render_quiz_screen()
elif current_step == "feedback":
    render_feedback_screen()
elif current_step in ["adaptive_lesson", "adaptive lesson"]:
    render_lesson_screen()
else:
    render_landing_screen()
