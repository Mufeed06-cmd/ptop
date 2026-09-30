"""
styles.py - Creative Visual Theme & UI Components for LearnMate AI
Gives Streamlit a high-end, futuristic EdTech SaaS look with glassmorphic cards,
glowing gradients, custom stepper, and responsive typography.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* Main canvas background */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(6, 182, 212, 0.08) 0%, transparent 40%),
                #0b0f19;
    color: #e2e8f0;
}

/* Hide default streamlit decorations */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom App Header Banner */
.lm-header {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 24px 30px;
    margin-bottom: 24px;
    backdrop-filter: blur(16px);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.lm-brand-title {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #a5b4fc 0%, #38bdf8 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 10px;
}

.lm-brand-subtitle {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 4px;
}

.lm-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

.lm-badge-timer {
    background: rgba(245, 158, 11, 0.15);
    color: #fcd34d;
    border-color: rgba(245, 158, 11, 0.3);
}

/* Stepper Progress Bar */
.lm-stepper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 12px 18px;
    margin-bottom: 28px;
    position: relative;
    overflow-x: auto;
}

.lm-step {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
    transition: all 0.3s ease;
    white-space: nowrap;
}

.lm-step.active {
    color: #38bdf8;
    text-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
}

.lm-step.completed {
    color: #10b981;
}

.lm-step-num {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    background: #1e293b;
    border: 1px solid #334155;
    color: #94a3b8;
}

.lm-step.active .lm-step-num {
    background: #0284c7;
    border-color: #38bdf8;
    color: #ffffff;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}

.lm-step.completed .lm-step-num {
    background: #059669;
    border-color: #34d399;
    color: #ffffff;
}

.lm-step-divider {
    flex: 1;
    height: 2px;
    background: #1e293b;
    margin: 0 10px;
    min-width: 20px;
}

/* Glassmorphic Card Containers */
.lm-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.lm-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
}

.lm-card-highlight {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(14, 165, 233, 0.05) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
}

.lm-card-danger {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(220, 38, 38, 0.03) 100%);
    border: 1px solid rgba(239, 68, 68, 0.35);
}

.lm-card-success {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.03) 100%);
    border: 1px solid rgba(16, 185, 129, 0.35);
}

/* Vernacular Language Callout Box */
.lm-vernacular-box {
    background: rgba(245, 158, 11, 0.07);
    border-left: 4px solid #f59e0b;
    border-radius: 0 12px 12px 0;
    padding: 14px 18px;
    margin: 16px 0;
    color: #fef3c7;
    font-size: 14px;
    line-height: 1.6;
}

/* Quiz Option Card Styling */
.lm-quiz-card {
    background: #131b2e;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.lm-quiz-card:hover {
    background: #1e293b;
    border-color: #38bdf8;
    transform: translateY(-2px);
}

/* Score Reveal Circle / Big Display */
.lm-score-circle {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 140px;
    height: 140px;
    border-radius: 50%;
    margin: 0 auto 20px auto;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 3px solid #6366f1;
    box-shadow: 0 0 25px rgba(99, 102, 241, 0.4);
}

.lm-score-val {
    font-size: 40px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1;
}

.lm-score-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin-top: 4px;
}

/* Weak Concept Pulse Tag */
.lm-weak-pulse {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 9999px;
    color: #fca5a5;
    font-size: 13px;
    font-weight: 600;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.85; transform: scale(1.02); }
}

/* Button overrides for Streamlit */
div.stButton > button {
    background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 12px 24px !important;
    font-size: 15px !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5) !important;
}

/* Secondary Button override */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4) !important;
}

/* Radio buttons & inputs enhancement */
div[data-testid="stRadio"] > div {
    gap: 12px;
}

div[data-testid="stRadio"] label {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 12px 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 100%;
}

div[data-testid="stRadio"] label:hover {
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.05);
}

/* Code block container */
pre, code {
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 8px !important;
}
</style>
"""

import textwrap

def render_stepper(current_step: int) -> str:
    """
    Renders the modern responsive 4-step progress header.
    current_step: 1 (Form) | 2 (Lesson) | 3 (Quiz) | 4 (Adaptive)
    """
    steps = [
        (1, "1. Setup & Goal", "🎯"),
        (2, "2. Micro-Lesson", "📖"),
        (3, "3. Checkpoint Quiz", "⚡"),
        (4, "4. AI Diagnosis", "🧠")
    ]
    
    html = ['<div class="lm-stepper">']
    for i, (num, label, icon) in enumerate(steps):
        if num < current_step:
            cls = "lm-step completed"
            badge = "✓"
        elif num == current_step:
            cls = "lm-step active"
            badge = str(num)
        else:
            cls = "lm-step"
            badge = str(num)
            
        html.append(f'<div class="{cls}"><div class="lm-step-num">{badge}</div><span>{icon} {label}</span></div>')
        if i < len(steps) - 1:
            html.append('<div class="lm-step-divider"></div>')
    html.append('</div>')
    return "".join(html)

def render_header(profile=None) -> str:
    """Renders the top branding card with dynamic badges without leading whitespace."""
    if profile:
        topic = getattr(profile, "topic", "Python loops")
        level = getattr(profile, "skill_level", getattr(profile, "level", "Beginner"))
        mins = getattr(profile, "minutes", getattr(profile, "time_minutes", 15))
        lang = getattr(profile, "language", "English")
        badge_html = (
            f'<div style="display: flex; gap: 8px; flex-wrap: wrap;">'
            f'<span class="lm-badge">🎯 {topic}</span>'
            f'<span class="lm-badge">📊 {level}</span>'
            f'<span class="lm-badge lm-badge-timer">⏱️ {mins} min sprint</span>'
            f'<span class="lm-badge">🗣️ {lang}</span>'
            f'</div>'
        )
    else:
        badge_html = (
            '<div style="display: flex; gap: 8px;">'
            '<span class="lm-badge">⚡ Nova Stack Sprint</span>'
            '<span class="lm-badge lm-badge-timer">⏱️ Real-time Adaptive Loop</span>'
            '</div>'
        )
        
    res = (
        '<div class="lm-header">'
        '<div>'
        '<div class="lm-brand-title"><span>✦</span> LearnMate AI</div>'
        '<div class="lm-brand-subtitle">Adaptive Time-Budgeted Mentor • Powered by Gemini & Nova Engine</div>'
        '</div>'
        f'{badge_html}'
        '</div>'
    )
    return res

