
import os
import json
import streamlit as st
def _load_gemini():
    try:
        from gemini_service import (
            ai_tutor as _ai_tutor,
            translate_text as _translate_text,
            correct_text as _correct_text,
            explain_word as _explain_word,
            generate_quiz as _generate_quiz,
            lesson_plan as _lesson_plan,
        )
        return (_ai_tutor, _translate_text, _correct_text,
                _explain_word, _generate_quiz, _lesson_plan)
    except Exception as exc:
        raise RuntimeError(
            "TongueTie AI module could not load. Make sure gemini_service.py "
            "is beside app.py and google-genai is listed in requirements.txt. "
            f"Details: {exc}"
        ) from exc

def ai_tutor(*args, **kwargs):
    return _load_gemini()[0](*args, **kwargs)

def translate_text(*args, **kwargs):
    return _load_gemini()[1](*args, **kwargs)

def correct_text(*args, **kwargs):
    return _load_gemini()[2](*args, **kwargs)

def explain_word(*args, **kwargs):
    return _load_gemini()[3](*args, **kwargs)

def generate_quiz(*args, **kwargs):
    return _load_gemini()[4](*args, **kwargs)

def lesson_plan(*args, **kwargs):
    return _load_gemini()[5](*args, **kwargs)
from language_data import LANGUAGES, language_options
from rag import retrieve_context
from speech_service import transcribe_audio, render_browser_tts

st.set_page_config(page_title="TongueTie", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

# ---------- Design ----------
st.markdown("""
<style>
:root { --bg:#050713; --panel:#10172d; --panel2:#151d38; --border:#293761;
        --text:#f8f9ff; --muted:#aab4d1; --a:#55c7ff; --b:#9b5cff; }
.stApp { background: radial-gradient(circle at 15% 0%, #18244b 0%, #050713 38%), #050713; color:var(--text); }
section[data-testid="stSidebar"] { background:#090e20; border-right:1px solid var(--border); }
.block-container { max-width: 1250px; padding-top: 1.4rem; }
h1,h2,h3 { color:var(--text)!important; }
.tt-hero { padding:28px; border:1px solid var(--border); border-radius:28px;
 background:linear-gradient(135deg,rgba(85,199,255,.13),rgba(155,92,255,.15)); }
.tt-title {font-size:48px;font-weight:800;letter-spacing:-2px;
 background:linear-gradient(90deg,#fff,#8bdcff,#a978ff);-webkit-background-clip:text;color:transparent;}
.tt-sub {color:var(--muted);font-size:17px;}
.card { background:rgba(16,23,45,.92); border:1px solid var(--border); border-radius:20px; padding:20px; margin:10px 0;}
.metric {font-size:28px;font-weight:800}.muted{color:var(--muted)}
.pill {display:inline-block;padding:7px 11px;border-radius:999px;background:#1c2747;color:#dbe5ff;margin:3px;font-size:12px}
div.stButton > button { border-radius:14px; border:1px solid #34436f; background:linear-gradient(90deg,#286c99,#6340a5);
 color:white; font-weight:700; min-height:44px; }
textarea,input { border-radius:14px!important; }
</style>
""", unsafe_allow_html=True)

def card(title, body):
    st.markdown(f'<div class="card"><h3>{title}</h3>{body}</div>', unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "words" not in st.session_state:
    st.session_state.words = []
if "lessons" not in st.session_state:
    st.session_state.lessons = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🌐 TongueTie")
    st.caption("Learn Languages. Speak Confidently. Understand the World.")
    page = st.radio("Navigate", [
        "Home", "Learn", "Voice Translator", "AI Tutor", "Correct My English",
        "Vocabulary", "Grammar", "Quiz & Tests", "Progress", "Profile", "Admin"
    ])
    st.divider()
    source = st.selectbox("I speak", language_options(), index=0)
    target = st.selectbox("I want to learn", language_options(), index=1)
    st.caption(f"{len(LANGUAGES)} language choices included")

# ---------- Header ----------
if page == "Home":
    st.markdown("""
    <div class="tt-hero">
      <div class="tt-title">TongueTie</div>
      <div class="tt-sub">Learn Languages. Speak Confidently. Understand the World.</div>
      <br>
      <span class="pill">100+ Languages</span><span class="pill">AI Tutor</span>
      <span class="pill">Voice Translation</span><span class="pill">Error Correction</span>
      <span class="pill">Female / Male Voice</span>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    c1,c2,c3,c4 = st.columns(4)
    for c, n, v in [(c1,"Lessons",st.session_state.lessons),(c2,"Words",len(st.session_state.words)),
                    (c3,"Quiz Score",f"{st.session_state.quiz_score}%"),(c4,"Languages",len(LANGUAGES))]:
        with c:
            card(n, f'<div class="metric">{v}</div><div class="muted">Your learning dashboard</div>')
    st.subheader("Quick Start")
    q1,q2,q3,q4 = st.columns(4)
    with q1:
        if st.button("🎙️ Voice Translator", use_container_width=True): st.session_state.page_jump="Voice Translator"; st.rerun()
    with q2:
        if st.button("🤖 AI Tutor", use_container_width=True): st.session_state.page_jump="AI Tutor"; st.rerun()
    with q3:
        if st.button("✍️ Correct Text", use_container_width=True): st.session_state.page_jump="Correct My English"; st.rerun()
    with q4:
        if st.button("📚 Start Lesson", use_container_width=True): st.session_state.page_jump="Learn"; st.rerun()
    st.info("Tip: for the richest voice experience, use the included browser prototype. Streamlit recording is available below in Voice Translator.")

elif page == "Learn":
    st.title("📚 Learn Any Language")
    st.caption(f"Learning {target} through {source}")
    level = st.selectbox("Level", ["Beginner", "Elementary", "Intermediate", "Upper Intermediate", "Advanced"])
    topic = st.text_input("Daily-life topic", "Introducing yourself")
    if st.button("Generate lesson"):
        with st.spinner("Building lesson..."):
            result = lesson_plan(source, target, level, topic)
        st.markdown(result)
        st.session_state.lessons += 1
    st.subheader("Learning path")
    for x in ["Daily conversation", "Vocabulary", "Grammar", "Pronunciation", "Listening", "Speaking", "Review"]:
        st.markdown(f"• {x}")

elif page == "Voice Translator":
    st.title("🎙️ Voice Translator")
    st.caption("Record speech, transcribe it, translate it, correct it, and listen back.")
    a,b,c = st.columns(3)
    with a: st.write(f"**From:** {source}")
    with b: st.write("⇄")
    with c: st.write(f"**To:** {target}")
    voice_gender = st.radio("Preferred voice", ["Female", "Male", "Browser default"], horizontal=True)
    st.caption("Female/male playback depends on the voices installed or enabled by the selected speech provider.")
    audio = st.audio_input("🎤 Tap to record")
    typed = st.text_area("Or enter text instead", placeholder="Speak or type a sentence...")
    if st.button("Translate & Analyze", type="primary"):
        text = typed.strip()
        if not text and audio:
            try:
                source_code = source.split("(")[-1].rstrip(")")
                with st.spinner("Listening and analyzing your speech..."):
                    text = transcribe_audio(audio.getvalue(), source_code)
                if not text:
                    st.error("No speech was detected. Please record again, speaking clearly.")
            except Exception as exc:
                st.error(f"Speech-to-text error: {exc}")
        if text:
            try:
                with st.spinner("Translating and checking..."):
                    result = translate_text(text, source, target)
                    correction = correct_text(text, source)
                st.markdown("### 📝 Speech transcript")
                st.info(text)
                st.markdown("### 🌐 Translation")
                st.markdown(result)
                st.markdown("### ✍️ Error correction")
                st.markdown(correction)
                st.session_state.history.insert(0, {"source":text,"from":source,"to":target,"result":result})
                st.session_state.last_translation = result
            except Exception as exc:
                st.error(f"AI analysis error: {exc}")
    st.divider()
    st.markdown("### 🔊 Voice playback")
    if st.session_state.get("last_translation"):
        target_code = target.split("(")[-1].rstrip(")")
        render_browser_tts(st.session_state.last_translation, target_code, voice_gender)
    else:
        st.caption("Translate text or speech first; the playback controls will appear here.")

elif page == "AI Tutor":
    st.title("🤖 AI Tutor")
    question = st.text_area("Ask your tutor", placeholder="Explain this grammar rule with simple examples...")
    if st.button("Ask Gemini", type="primary") and question.strip():
        context = retrieve_context(question)
        with st.spinner("Thinking..."):
            answer = ai_tutor(question, source, target, context)
        st.markdown(answer)

elif page == "Correct My English":
    st.title("✍️ Correct My Text")
    text = st.text_area("Write a sentence or paragraph", height=180,
                        placeholder="I go to market yesterday and buyed some food.")
    if st.button("Correct & Explain", type="primary") and text.strip():
        with st.spinner("Checking grammar, spelling and naturalness..."):
            st.markdown(correct_text(text, target))
        st.caption("Correction is language-learning guidance; always review suggestions for context and dialect.")

elif page == "Vocabulary":
    st.title("📖 Vocabulary Builder")
    word = st.text_input("Word or difficult phrase", placeholder="opportunity")
    if st.button("Analyze word", type="primary") and word.strip():
        with st.spinner("Analyzing..."):
            out = explain_word(word, source, target)
        if str(out).startswith("AI service error:"):
            st.error(out)
        else:
            st.markdown(out)
        if st.button("➕ Add to My Words"):
            st.session_state.words.append(word)
    if st.session_state.words:
        st.subheader("My words")
        st.write(" · ".join(dict.fromkeys(st.session_state.words)))

elif page == "Grammar":
    st.title("🧠 Grammar Guide")
    topic = st.text_input("Grammar topic", "Present simple tense")
    if st.button("Explain grammar", type="primary"):
        with st.spinner("Preparing clear explanation..."):
            st.markdown(ai_tutor(f"Teach {topic} with simple rules, examples, common mistakes and a mini exercise.",
                                 source, target, retrieve_context(topic)))

elif page == "Quiz & Tests":
    st.title("🧪 Quiz & Tests")
    topic = st.text_input("Quiz topic", "Daily conversation")
    if st.button("Generate quiz", type="primary"):
        with st.spinner("Generating quiz..."):
            st.session_state.quiz = generate_quiz(source, target, topic)
    if "quiz" in st.session_state:
        st.markdown(st.session_state.quiz)
        st.number_input("Enter your score (%)", 0, 100, st.session_state.quiz_score, key="score_input")
        if st.button("Save score"):
            st.session_state.quiz_score = int(st.session_state.score_input)

elif page == "Progress":
    st.title("📊 My Progress")
    c1,c2,c3 = st.columns(3)
    c1.metric("Lessons", st.session_state.lessons)
    c2.metric("Words", len(st.session_state.words))
    c3.metric("Quiz", f"{st.session_state.quiz_score}%")
    st.progress(min(st.session_state.lessons/20,1.0), text="Learning path progress")

elif page == "Profile":
    st.title("👤 Profile")
    name = st.text_input("Name", "TongueTie Learner")
    st.write(f"Native language: **{source}**")
    st.write(f"Learning language: **{target}**")
    st.checkbox("Daily reminders", True)
    st.checkbox("Show pronunciation tips", True)
    st.checkbox("Prefer female voice when available", True)

elif page == "Admin":
    st.title("⚙️ Admin Dashboard")
    password = st.text_input("Admin password", type="password")
    expected = os.getenv("TONGUETIE_ADMIN_PASSWORD", "")
    if expected and password == expected:
        st.success("Admin access granted.")
        cols = st.columns(4)
        cols[0].metric("Users", "—")
        cols[1].metric("Lessons", "—")
        cols[2].metric("Languages", len(LANGUAGES))
        cols[3].metric("AI/RAG", "Ready")
        st.subheader("Admin modules")
        st.write("Users • Content • Languages • AI & RAG • Quizzes & Tests • Analytics • Reports • Settings")
    elif expected:
        st.info("Enter the password configured in the environment variable TONGUETIE_ADMIN_PASSWORD.")
    else:
        st.warning("Admin password is not configured. Set TONGUETIE_ADMIN_PASSWORD in your deployment secrets/environment.")

# Optional page jump from quick buttons
if "page_jump" in st.session_state:
    del st.session_state.page_jump
