from __future__ import annotations

import os
import streamlit as st

from language_data import LANGUAGES, language_options
from rag import retrieve_context
from gemini_service import (
    ai_tutor,
    translate_text,
    correct_text,
    explain_word,
    generate_quiz,
    lesson_plan,
)
from speech_service import transcribe_audio, render_browser_tts


st.set_page_config(
    page_title="TongueTie — AI Language Studio",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Design system ----------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#070b18;--panel:#10172b;--panel2:#141d36;--line:#27375e;--text:#f7f8ff;--muted:#9eabd0;--cyan:#55d8ff;--violet:#8b5cf6;--pink:#ec70d7;--green:#51e6ad;}
html,body,[class*="css"]{font-family:Inter,system-ui,sans-serif}
.stApp{background:radial-gradient(circle at 8% -5%,#24386c 0%,transparent 32%),radial-gradient(circle at 95% 8%,#3b174b 0%,transparent 27%),var(--bg);color:var(--text)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1022,#080c19);border-right:1px solid var(--line)}
.block-container{max-width:1260px;padding:1.2rem 1.4rem 3rem}
h1,h2,h3,h4,p,label{color:var(--text)!important}
.stCaption,.muted{color:var(--muted)!important}
.tt-top{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border:1px solid var(--line);background:rgba(16,23,43,.72);backdrop-filter:blur(16px);border-radius:22px;margin-bottom:16px}
.brand{font-weight:800;font-size:24px;letter-spacing:-.8px}.brand span{background:linear-gradient(90deg,var(--cyan),#fff,var(--pink));-webkit-background-clip:text;color:transparent}
.badge{padding:7px 11px;border:1px solid #35507f;background:#121d39;border-radius:999px;color:#cdd9ff;font-size:12px}
.hero{position:relative;overflow:hidden;padding:34px;border:1px solid #324674;border-radius:30px;background:linear-gradient(135deg,rgba(40,109,153,.32),rgba(111,64,190,.22) 55%,rgba(236,112,215,.12));box-shadow:0 24px 80px rgba(0,0,0,.28)}
.hero:after{content:"";position:absolute;width:260px;height:260px;right:-80px;top:-100px;border-radius:50%;background:rgba(85,216,255,.16);filter:blur(20px)}
.hero h1{font-size:clamp(40px,7vw,68px);line-height:.98;margin:0 0 14px;font-weight:800;letter-spacing:-3px}
.gradient{background:linear-gradient(90deg,#fff,var(--cyan),#b58aff,var(--pink));-webkit-background-clip:text;color:transparent}
.hero p{font-size:17px;color:#c5cce5!important;max-width:720px;line-height:1.6}
.pillrow{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.pill{padding:8px 12px;border-radius:999px;background:rgba(9,15,34,.48);border:1px solid #3b4c79;color:#dbe5ff;font-size:12px}
.section-title{font-size:22px;font-weight:800;margin:24px 0 10px}
.card{height:100%;padding:20px;border-radius:22px;border:1px solid var(--line);background:linear-gradient(180deg,rgba(20,29,54,.88),rgba(12,18,36,.88));box-shadow:0 14px 40px rgba(0,0,0,.18)}
.card h3{margin:0 0 8px;font-size:17px}.card p{color:var(--muted)!important;font-size:13px;line-height:1.55}
.metric{font-size:30px;font-weight:800;margin-top:5px}.metric-label{font-size:12px;color:var(--muted)}
.feature-icon{font-size:28px;margin-bottom:8px}
div.stButton>button{border:1px solid #42619b;border-radius:14px;min-height:44px;background:linear-gradient(90deg,#236d9b,#7141c7);color:#fff;font-weight:700;box-shadow:0 8px 24px rgba(69,65,180,.22)}
div.stButton>button:hover{border-color:#7de2ff;transform:translateY(-1px)}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{background:#151b2d!important;border:1px solid #303f67!important;color:#fff!important;border-radius:14px!important}
[data-testid="stMetric"]{background:#11182c;border:1px solid var(--line);padding:12px;border-radius:18px}
.tt-result{padding:18px;border-radius:20px;border:1px solid #33466f;background:linear-gradient(135deg,#111b34,#15152d);margin:10px 0}
.success{border-color:#2e8068;background:linear-gradient(135deg,rgba(32,104,82,.22),rgba(15,24,44,.9))}
.sidebar-brand{padding:8px 4px 16px}.sidebar-brand strong{font-size:22px}.sidebar-brand small{display:block;color:var(--muted);line-height:1.4;margin-top:4px}
footer{visibility:hidden}
</style>
""",
    unsafe_allow_html=True,
)


def code_of(label: str) -> str:
    return label.split("(")[-1].rstrip(")").strip()


def feature(title: str, icon: str, text: str):
    st.markdown(
        f'<div class="card"><div class="feature-icon">{icon}</div><h3>{title}</h3><p>{text}</p></div>',
        unsafe_allow_html=True,
    )


def show_ai_result(result: str):
    if str(result).startswith("AI service error:"):
        st.error(result)
    else:
        st.markdown(f'<div class="tt-result">{result}</div>', unsafe_allow_html=True)


for key, default in {"history": [], "words": [], "lessons": 0, "quiz_score": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- Navigation ----------------
with st.sidebar:
    st.markdown('<div class="sidebar-brand"><strong>🌍 Tongue<span style="color:#8b5cf6">Tie</span></strong><small>AI Language Studio<br>Learn • Speak • Understand</small></div>', unsafe_allow_html=True)
    page = st.radio(
        "Workspace",
        ["Home", "Learn", "Voice Translator", "AI Tutor", "Correct My English", "Vocabulary", "Grammar", "Quiz & Tests", "Progress", "Profile", "Admin"],
        label_visibility="collapsed",
    )
    st.divider()
    source = st.selectbox("I speak", language_options(), index=0)
    target = st.selectbox("I want to learn", language_options(), index=1)
    st.markdown(f'<span class="badge">{len(LANGUAGES)} languages</span>', unsafe_allow_html=True)

# ---------------- Top bar ----------------
st.markdown(
    f'<div class="tt-top"><div class="brand">🌍 <span>TongueTie</span></div><div><span class="badge">{source} → {target}</span></div></div>',
    unsafe_allow_html=True,
)

# ---------------- Pages ----------------
if page == "Home":
    st.markdown(
        '<div class="hero"><h1>Speak beyond<br><span class="gradient">language barriers.</span></h1><p>Learn languages with an AI tutor, real speech transcription, instant translation, smart correction, vocabulary practice and guided lessons — all in one creative workspace.</p><div class="pillrow"><span class="pill">100+ Languages</span><span class="pill">AI Tutor</span><span class="pill">Voice AI</span><span class="pill">Grammar Coach</span><span class="pill">Personal Progress</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">Your learning snapshot</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    stats = [("Lessons", st.session_state.lessons), ("Words", len(st.session_state.words)), ("Quiz score", f"{st.session_state.quiz_score}%"), ("Languages", len(LANGUAGES))]
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(f'<div class="card"><div class="metric">{value}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Explore TongueTie</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]: feature("Voice Translator", "🎙️", "Record speech, transcribe it, translate it and check grammar.")
    with cols[1]: feature("AI Tutor", "🤖", "Ask questions and practice naturally with context-aware help.")
    with cols[2]: feature("Vocabulary", "📖", "Turn difficult words into examples, synonyms and practice.")
    with cols[3]: feature("Daily Lessons", "🚀", "Follow short lessons designed around your level and goals.")

elif page == "Learn":
    st.title("📚 Learning Studio")
    st.caption(f"Learning {target} through {source}")
    left, right = st.columns([1, 1])
    with left:
        level = st.selectbox("Level", ["Beginner", "Elementary", "Intermediate", "Upper Intermediate", "Advanced"])
        topic = st.text_input("Daily-life topic", "Introducing yourself")
        if st.button("✨ Generate lesson", type="primary", use_container_width=True):
            with st.spinner("Building your lesson..."):
                result = lesson_plan(source, target, level, topic)
            show_ai_result(result)
            if not str(result).startswith("AI service error:"):
                st.session_state.lessons += 1
    with right:
        feature("Learning path", "🧭", "Daily conversation → Vocabulary → Grammar → Pronunciation → Listening → Speaking → Review")

elif page == "Voice Translator":
    st.title("🎙️ Voice Translator")
    st.caption("Your voice → transcript → translation → correction → playback")
    a, b = st.columns(2)
    with a:
        st.markdown(f'<div class="card"><h3>🎤 Speak in</h3><p>{source}</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown(f'<div class="card"><h3>🌐 Translate to</h3><p>{target}</p></div>', unsafe_allow_html=True)
    voice_gender = st.radio("Playback voice", ["Female", "Male", "Browser default"], horizontal=True)
    audio = st.audio_input("🎤 Tap to record")
    typed = st.text_area("Or type a sentence", placeholder="Say or type something to translate...")
    if st.button("🚀 Analyze & Translate", type="primary", use_container_width=True):
        text = typed.strip()
        if not text and audio:
            with st.spinner("Listening to your recording..."):
                text = transcribe_audio(audio.getvalue(), code_of(source))
        if not text:
            st.warning("No speech detected. Please record again or type your sentence.")
        else:
            with st.spinner("AI is translating and checking your speech..."):
                translation = translate_text(text, source, target)
                correction = correct_text(text, source)
            st.markdown('<div class="section-title">Analysis</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tt-result"><b>📝 Transcript</b><br>{text}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tt-result"><b>🌐 Translation</b><br>{translation}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tt-result success"><b>✍️ Correction</b><br>{correction}</div>', unsafe_allow_html=True)
            if not str(translation).startswith("AI service error:"):
                st.session_state.history.insert(0, {"source": text, "from": source, "to": target, "result": translation})
                st.session_state.last_translation = translation
    if st.session_state.get("last_translation"):
        st.markdown('<div class="section-title">🔊 Listen</div>', unsafe_allow_html=True)
        render_browser_tts(st.session_state.last_translation, code_of(target), voice_gender)

elif page == "AI Tutor":
    st.title("🤖 AI Tutor")
    st.caption("Ask naturally. Get examples. Practice immediately.")
    question = st.text_area("Your question", placeholder="Explain when to use the present simple in easy English...")
    if st.button("Ask Tutor", type="primary") and question.strip():
        with st.spinner("Your tutor is thinking..."):
            show_ai_result(ai_tutor(question, source, target, retrieve_context(question)))

elif page == "Correct My English":
    st.title("✍️ Smart Correction")
    text = st.text_area("Write a sentence or paragraph", height=190, placeholder="I am happy not goof")
    if st.button("Correct & Explain", type="primary") and text.strip():
        with st.spinner("Checking grammar, spelling and naturalness..."):
            show_ai_result(correct_text(text, target))

elif page == "Vocabulary":
    st.title("📖 Vocabulary Builder")
    word = st.text_input("Word or difficult phrase", placeholder="opportunity")
    if st.button("Analyze word", type="primary") and word.strip():
        with st.spinner("Building your word card..."):
            result = explain_word(word, source, target)
        show_ai_result(result)
        if not str(result).startswith("AI service error:"):
            if st.button("➕ Add to My Words"):
                st.session_state.words.append(word)
    if st.session_state.words:
        st.markdown('<div class="section-title">My Words</div>', unsafe_allow_html=True)
        st.write(" · ".join(dict.fromkeys(st.session_state.words)))

elif page == "Grammar":
    st.title("🧠 Grammar Coach")
    topic = st.text_input("Grammar topic", "Present simple tense")
    if st.button("Explain grammar", type="primary"):
        with st.spinner("Preparing a simple explanation..."):
            show_ai_result(ai_tutor(f"Teach {topic} with simple rules, examples, common mistakes and a mini exercise.", source, target, retrieve_context(topic)))

elif page == "Quiz & Tests":
    st.title("🧪 Quiz Lab")
    topic = st.text_input("Quiz topic", "Daily conversation")
    if st.button("Generate quiz", type="primary"):
        with st.spinner("Creating your quiz..."):
            st.session_state.quiz = generate_quiz(source, target, topic)
    if "quiz" in st.session_state:
        show_ai_result(st.session_state.quiz)
        score = st.number_input("Your score (%)", 0, 100, st.session_state.quiz_score)
        if st.button("Save score"):
            st.session_state.quiz_score = int(score)

elif page == "Progress":
    st.title("📊 My Progress")
    c1, c2, c3 = st.columns(3)
    c1.metric("Lessons", st.session_state.lessons)
    c2.metric("Words", len(st.session_state.words))
    c3.metric("Quiz", f"{st.session_state.quiz_score}%")
    st.progress(min(st.session_state.lessons / 20, 1.0), text="Learning path progress")
    if st.session_state.history:
        st.subheader("Recent practice")
        for item in st.session_state.history[:5]:
            st.markdown(f'<div class="card"><b>{item["from"]} → {item["to"]}</b><p>{item["source"]}</p></div>', unsafe_allow_html=True)

elif page == "Profile":
    st.title("👤 Profile & Preferences")
    name = st.text_input("Name", "TongueTie Learner")
    st.markdown(f'<div class="card"><h3>{name}</h3><p>Native: {source}<br>Learning: {target}</p></div>', unsafe_allow_html=True)
    st.checkbox("Daily reminders", True)
    st.checkbox("Show pronunciation tips", True)
    st.checkbox("Prefer female voice when available", True)

elif page == "Admin":
    st.title("⚙️ Admin Studio")
    password = st.text_input("Admin password", type="password")
    expected = os.getenv("TONGUETIE_ADMIN_PASSWORD", "")
    try:
        if not expected:
            expected = st.secrets.get("TONGUETIE_ADMIN_PASSWORD", "")
    except Exception:
        pass
    if expected and password == expected:
        st.success("Admin access granted.")
        cols = st.columns(4)
        cols[0].metric("Languages", len(LANGUAGES))
        cols[1].metric("Words", len(st.session_state.words))
        cols[2].metric("Lessons", st.session_state.lessons)
        cols[3].metric("AI", "REST")
        st.subheader("Management")
        st.write("Users • Content • Languages • AI & RAG • Quizzes • Analytics • Reports • Settings")
    elif expected:
        st.info("Enter the configured admin password.")
    else:
        st.warning("Configure TONGUETIE_ADMIN_PASSWORD in Streamlit Secrets.")
