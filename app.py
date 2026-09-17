from __future__ import annotations

import os
import streamlit as st

from language_data import LANGUAGES, language_options, POPULAR, PROFICIENCY_LEVELS
from rag import retrieve_context
from gemini_service import (
    ai_tutor,
    translate_text,
    translate_fast,
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
    initial_sidebar_state="collapsed",
)

# ==================================================================================
# Design system — dark glass + cyan/violet gradient, matching the TongueTie mock-ups
# ==================================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#050713;--panel:#10172d;--panel2:#141d36;--line:#293761;
  --text:#f8f9ff;--muted:#aab4d1;--cyan:#55c7ff;--violet:#9b5cff;--pink:#ec70d7;--green:#51e6ad;
}
html,body,[class*="css"]{font-family:'Inter',system-ui,sans-serif}
.stApp{
  background:
    radial-gradient(circle at 10% -8%, rgba(85,199,255,.16) 0%, transparent 30%),
    radial-gradient(circle at 96% 6%, rgba(155,92,255,.18) 0%, transparent 28%),
    radial-gradient(circle at 50% 100%, rgba(236,112,215,.08) 0%, transparent 35%),
    var(--bg);
  color:var(--text);
}
.block-container{max-width:1280px;padding:1.1rem 1.4rem 3rem}
h1,h2,h3,h4,p,label,span{color:var(--text)}
.stCaption,.muted{color:var(--muted)!important}
footer{visibility:hidden}
#MainMenu{visibility:hidden}

/* ---------- Sidebar = the "side tab" panel: languages, quick-picks, switches ---------- */
section[data-testid="stSidebar"]{display:none!important}
.front-controls{padding:16px;border:1px solid var(--line);border-radius:22px;background:rgba(16,23,43,.78);backdrop-filter:blur(16px);margin-bottom:14px}
.control-label{font-size:11px;font-weight:800;color:#8fa0c8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px}
.nav-caption{font-size:12px;color:#8fa0c8;margin:0 0 7px 2px}
.voice-title{font-size:28px;font-weight:900;letter-spacing:-1px;margin-bottom:4px}
.voice-sub{color:#9eacd0;font-size:13px;margin-bottom:14px}


/* ---------- Voice Studio: single, unified "plugin" style voice-recognition panel ---------- */
.voice-studio{position:relative;border:1px solid #3d6ea8;border-radius:26px 26px 0 0;border-bottom:none;padding:6px 18px 4px;margin:8px 0 0;
  background:linear-gradient(160deg,rgba(20,45,70,.55),rgba(56,32,96,.42));box-shadow:0 18px 46px rgba(0,0,0,.28)}
.voice-studio-head{display:flex;align-items:center;gap:8px;padding:12px 2px 0}
.vs-dot{width:9px;height:9px;border-radius:50%;background:#51e6ad;box-shadow:0 0 10px #51e6ad;animation:pulse 2.2s ease-in-out infinite}
.vs-name{font-weight:800;font-size:13.5px;letter-spacing:.2px}
.vs-tag{margin-left:auto;font-size:10.5px;font-weight:700;color:#bcd2ff;background:rgba(85,199,255,.14);
  border:1px solid rgba(125,226,255,.3);padding:3px 9px;border-radius:999px}
/* The recorder below is a separate Streamlit block; these rules make it read as
   one continuous panel with .voice-studio rather than actually nesting it. */
.voice-studio + div[data-testid="stAudioInput"]{
  border:1px solid #3d6ea8;border-top:none;border-radius:0 0 26px 26px;
  background:linear-gradient(160deg,rgba(20,45,70,.4),rgba(56,32,96,.32));
  margin-top:-2px;margin-bottom:14px;padding:14px}

.sidebar-brand{padding:6px 2px 14px;display:flex;align-items:center;gap:10px}
.sidebar-brand .logo-ring{position:relative;width:38px;height:38px;flex:0 0 38px}
.sidebar-brand .logo-ring .ring{position:absolute;inset:0;border-radius:50%;
  background:radial-gradient(circle,rgba(85,199,255,.55),transparent 70%);animation:pulse 2.2s ease-in-out infinite}
.sidebar-brand .logo-ring .dot{position:absolute;inset:6px;border-radius:50%;
  background:linear-gradient(135deg,var(--cyan),var(--violet));display:flex;align-items:center;justify-content:center;
  box-shadow:0 6px 18px rgba(122,90,255,.5)}
.sidebar-brand .logo-ring svg{width:14px;height:14px;fill:#0a0e1c}
.sidebar-brand strong{font-size:20px;letter-spacing:-.5px}
.sidebar-brand small{display:block;color:var(--muted);line-height:1.4;font-size:11px}
@keyframes pulse{0%{transform:scale(.75);opacity:.9}50%{transform:scale(1.35);opacity:.25}100%{transform:scale(.75);opacity:.9}}

.chip-row{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px;cursor:grab}
.chip{padding:6px 10px;border-radius:999px;background:#141d38;border:1px solid #2c3c68;
  color:#dbe5ff;font-size:11.5px;font-weight:600;user-select:none;transition:transform .12s,border-color .12s}
.chip:active{cursor:grabbing;transform:scale(.96)}
.chip.dragging{opacity:.45}
.chip:hover{border-color:#7de2ff}

/* ---------- Top pill tab-bar (the primary, always-visible navigation) ---------- */
.tt-top{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  padding:14px 20px;border:1px solid var(--line);background:rgba(16,23,43,.72);
  backdrop-filter:blur(16px);border-radius:22px;margin-bottom:14px}
.brand{font-weight:900;font-size:23px;letter-spacing:-.8px;display:flex;align-items:center;gap:10px}
.brand .gtext{background:linear-gradient(90deg,var(--cyan),#fff,var(--pink));-webkit-background-clip:text;color:transparent}
.badge{padding:7px 12px;border:1px solid #35507f;background:#121d39;border-radius:999px;color:#cdd9ff;font-size:12px;font-weight:600}
.badge.live{border-color:#2c8f6c;color:#7cf0c0}

/* ---------- Modern floating "dock" for the primary nav row + "More tools" select ----------
   .nav-dock is an empty marker div; the following two Streamlit blocks (the
   5-button row, then the selectbox) are its DOM siblings, styled via
   adjacent-sibling selectors — no custom classes on Streamlit's own
   containers needed, so this stays robust across Streamlit versions. */
.nav-dock{height:8px;margin:0 0 -4px;border-radius:20px 20px 0 0;border:1px solid #2c3d68;border-bottom:none;
  background:linear-gradient(135deg,rgba(13,19,38,.85),rgba(18,14,34,.85))}
.nav-dock + div[data-testid="stHorizontalBlock"]{
  border:1px solid #2c3d68;border-bottom:none;border-radius:0;padding:6px 8px 2px;
  background:linear-gradient(135deg,rgba(13,19,38,.85),rgba(18,14,34,.85));backdrop-filter:blur(18px);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
.nav-dock + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button{
  border:1px solid transparent;border-radius:14px;min-height:38px;font-size:13px;
  background:transparent;color:#aab9e6;font-weight:700;box-shadow:none}
.nav-dock + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover{
  background:rgba(85,199,255,.10);color:#fff;transform:none;border-color:rgba(125,226,255,.35)}
.nav-dock + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"]{
  background:linear-gradient(90deg,var(--cyan),var(--violet));color:#0a0e1c;border-color:transparent;
  box-shadow:0 8px 22px rgba(122,90,255,.4)}
.nav-dock + div[data-testid="stHorizontalBlock"] + div[data-testid="stSelectbox"]{
  border:1px solid #2c3d68;border-top:none;border-radius:0 0 20px 20px;
  background:linear-gradient(135deg,rgba(13,19,38,.85),rgba(18,14,34,.85));
  padding:8px 10px 12px;margin-bottom:14px;box-shadow:0 18px 40px rgba(0,0,0,.28)}

div[data-testid="stButton"] button{
  border:1px solid #42619b;border-radius:14px;min-height:42px;
  background:linear-gradient(90deg,#1c3f66,#241a4a);color:#cfe0ff;font-weight:700;
  box-shadow:0 6px 18px rgba(20,20,50,.18);transition:transform .12s,box-shadow .12s,border-color .12s}
div[data-testid="stButton"] button:hover{border-color:#7de2ff;transform:translateY(-2px)}
div[data-testid="stButton"] button[kind="primary"]{
  background:linear-gradient(90deg,#236d9b,#7141c7);color:#fff;border-color:#8fd7ff;
  box-shadow:0 10px 26px rgba(103,90,220,.35)}

.stTextInput input,.stTextArea textarea,.stNumberInput input,
.stSelectbox div[data-baseweb="select"]>div{
  background:#151b2d!important;border:1px solid #303f67!important;color:#fff!important;border-radius:14px!important}

/* Toggle switches ("switches" requested in the UI) get the brand gradient when on */
[data-testid="stToggle"] label div[data-baseweb="checkbox"] div[aria-checked="true"]{
  background:linear-gradient(90deg,var(--cyan),var(--violet))!important;border-color:transparent!important}

.hero{position:relative;overflow:hidden;padding:34px;border:1px solid #324674;border-radius:30px;
  background:linear-gradient(135deg,rgba(40,109,153,.32),rgba(111,64,190,.22) 55%,rgba(236,112,215,.12));
  box-shadow:0 24px 80px rgba(0,0,0,.28)}
.hero:after{content:"";position:absolute;width:260px;height:260px;right:-80px;top:-100px;border-radius:50%;
  background:rgba(85,216,255,.16);filter:blur(20px)}
.hero h1{font-size:clamp(36px,6vw,60px);line-height:1.02;margin:0 0 12px;font-weight:900;letter-spacing:-2.5px}
.gradient{background:linear-gradient(90deg,#fff,var(--cyan),#b58aff,var(--pink));-webkit-background-clip:text;color:transparent}
.hero p{font-size:16.5px;color:#c5cce5!important;max-width:720px;line-height:1.6}
.pillrow{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.pill{padding:8px 12px;border-radius:999px;background:rgba(9,15,34,.48);border:1px solid #3b4c79;color:#dbe5ff;font-size:12px}

.section-title{font-size:21px;font-weight:800;margin:22px 0 10px}

/* Cards lift and glow on hover: the "movable" / alive feel across the app */
.card{height:100%;padding:20px;border-radius:22px;border:1px solid var(--line);
  background:linear-gradient(180deg,rgba(20,29,54,.88),rgba(12,18,36,.88));
  box-shadow:0 14px 40px rgba(0,0,0,.18);transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}
.card:hover{transform:translateY(-6px) scale(1.012);border-color:#5f86d6;box-shadow:0 22px 50px rgba(85,140,255,.18)}
.card h3{margin:0 0 8px;font-size:16.5px}.card p{color:var(--muted)!important;font-size:13px;line-height:1.55}
.metric{font-size:29px;font-weight:800;margin-top:4px}.metric-label{font-size:12px;color:var(--muted)}
.feature-icon{font-size:27px;margin-bottom:8px}

[data-testid="stMetric"]{background:#11182c;border:1px solid var(--line);padding:12px;border-radius:18px}
.tt-result{padding:18px;border-radius:20px;border:1px solid #33466f;background:linear-gradient(135deg,#111b34,#15152d);margin:10px 0}
.success{border-color:#2e8068;background:linear-gradient(135deg,rgba(32,104,82,.22),rgba(15,24,44,.9))}

/* ---------- Big, real, visible microphone centerpiece for Voice Translator ---------- */
.mic-stage{display:flex;flex-direction:column;align-items:center;padding:18px 10px 8px}
.mic-orb{position:relative;width:140px;height:140px;display:flex;align-items:center;justify-content:center;margin-bottom:6px}
.mic-orb .r1,.mic-orb .r2{position:absolute;inset:0;border-radius:50%;border:2px solid rgba(85,199,255,.35)}
.mic-orb .r1{animation:orb 2.6s ease-out infinite}
.mic-orb .r2{animation:orb 2.6s ease-out infinite;animation-delay:1.1s}
@keyframes orb{0%{transform:scale(.55);opacity:.9}100%{transform:scale(1.35);opacity:0}}
.mic-orb .core{position:relative;width:86px;height:86px;border-radius:50%;
  background:linear-gradient(135deg,var(--cyan),var(--violet));display:flex;align-items:center;justify-content:center;
  box-shadow:0 14px 40px rgba(122,90,255,.55)}
.mic-orb .core svg{width:34px;height:34px;fill:#0a0e1c}
.mic-caption{color:var(--muted);font-size:12.5px;letter-spacing:.3px}

/* Native Streamlit audio recorder, restyled to sit inside the mic stage */
div[data-testid="stAudioInput"]{
  border:1px solid #33466f;border-radius:20px;background:rgba(13,20,40,.7);padding:10px;margin-top:6px}

/* Segmented pill tab bar built from st.button columns */
.tabbar-wrap{margin-bottom:4px}
</style>
""",
    unsafe_allow_html=True,
)


MIC_SVG = '<svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z"/></svg>'


def code_of(label: str) -> str:
    return label.split("(")[-1].rstrip(")").strip()


def name_of(label: str) -> str:
    return label.split("(")[0].strip()


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


defaults = {
    "history": [], "words": [], "lessons": 0, "quiz_score": 0,
    "page": "Home",
    "autoplay": False, "prefer_female": True,
    "proficiency": PROFICIENCY_LEVELS[1],
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

PAGES = [
    ("Home", "🏠"), ("Learn", "📚"), ("Voice Translator", "🎙️"), ("AI Tutor", "🤖"),
    ("Correct My English", "✍️"), ("Vocabulary", "📖"), ("Grammar", "🧠"),
    ("Quiz & Tests", "🧪"), ("Progress", "📊"), ("Profile", "👤"), ("Admin", "⚙️"),
]

# ---------------- Front controls: no sidebar ----------------
def _swap_languages():
    opts = language_options()
    st.session_state.source_lang, st.session_state.target_lang = (
        st.session_state.get("target_lang", opts[1]),
        st.session_state.get("source_lang", opts[0]),
    )

source = st.session_state.get("source_lang", language_options()[0])
target = st.session_state.get("target_lang", language_options()[1])

st.markdown('<div class="front-controls">', unsafe_allow_html=True)
left, swap, right = st.columns([5,1,5])
with left:
    st.markdown('<div class="control-label">I speak</div>', unsafe_allow_html=True)
    source = st.selectbox("Source", language_options(), index=language_options().index(source) if source in language_options() else 0, label_visibility="collapsed", key="source_lang")
with swap:
    st.markdown('<div style="height:23px"></div>', unsafe_allow_html=True)
    st.button("⇄", use_container_width=True, key="swap_btn", on_click=_swap_languages)
with right:
    st.markdown('<div class="control-label">I am learning</div>', unsafe_allow_html=True)
    target = st.selectbox("Target", language_options(), index=language_options().index(target) if target in language_options() else 1, label_visibility="collapsed", key="target_lang")
st.markdown(f'<div style="margin-top:8px"><span class="badge">🌍 {len(LANGUAGES)} languages</span> <span class="badge live">● AI ready</span></div></div>', unsafe_allow_html=True)

# ---------------- Top brand bar ----------------
st.markdown(
    f'<div class="tt-top"><div class="brand">'
    f'<div class="logo-ring" style="width:30px;height:30px;flex:0 0 30px"><div class="ring"></div>'
    f'<div class="dot" style="inset:4px">{MIC_SVG}</div></div>'
    f'<span class="gtext">TongueTie</span></div>'
    f'<div style="display:flex;gap:8px;flex-wrap:wrap"><span class="badge">{name_of(source)} → {name_of(target)}</span>'
    f'<span class="badge live">● Gemini connected</span></div></div>',
    unsafe_allow_html=True,
)

# ---------------- Primary navigation: clean front tabs ----------------
st.markdown('<div class="nav-dock"></div>', unsafe_allow_html=True)
primary = [("Home","🏠"),("Learn","📚"),("Voice Translator","🎙️"),("AI Tutor","🤖"),("Correct My English","✍️")]
cols = st.columns(5)
for col, (name, icon) in zip(cols, primary):
    with col:
        if st.button(f"{icon} {name if name != 'Correct My English' else 'Practice'}", key=f"nav_{name}", use_container_width=True, type="primary" if st.session_state.page == name else "secondary"):
            st.session_state.page = name
            st.rerun()
more = [x for x in PAGES if x[0] not in {n for n,_ in primary}]
more_names = [f"{i} {n}" for n,i in more]
selected_more = st.selectbox("More tools", ["More…"] + more_names, label_visibility="collapsed", key="more_nav")
if selected_more != "More…":
    chosen = selected_more.split(" ",1)[1]
    if st.session_state.page != chosen:
        st.session_state.page = chosen
        st.rerun()
page = st.session_state.page

# ---------------- Pages ----------------
if page == "Home":
    st.markdown(
        '<div class="hero"><h1>Speak beyond<br><span class="gradient">language barriers.</span></h1>'
        '<p>Learn languages with an AI tutor, real speech recognition, instant translation, smart correction, '
        'vocabulary practice and guided lessons — all in one fast, creative workspace.</p>'
        '<div class="pillrow"><span class="pill">250+ Languages</span><span class="pill">AI Tutor</span>'
        '<span class="pill">AI Voice Recognition</span><span class="pill">Grammar Coach</span>'
        '<span class="pill">Personal Progress</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">Your learning snapshot</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    stats = [("Lessons", st.session_state.lessons), ("Words", len(st.session_state.words)),
             ("Quiz score", f"{st.session_state.quiz_score}%"), ("Languages", len(LANGUAGES))]
    for col, (label, value) in zip(cols, stats):
        with col:
            st.markdown(f'<div class="card"><div class="metric">{value}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Explore TongueTie</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]: feature("Voice Translator", "🎙️", "Speak live, get an instant transcript, translation, correction and playback.")
    with cols[1]: feature("AI Tutor", "🤖", "Ask questions and practice naturally with context-aware help.")
    with cols[2]: feature("Vocabulary", "📖", "Turn difficult words into examples, synonyms and practice.")
    with cols[3]: feature("Daily Lessons", "🚀", "Follow short lessons designed around your level and goals.")

elif page == "Learn":
    st.title("📚 Learning Studio")
    st.caption(f"Learning {name_of(target)} through {name_of(source)} · Level: {st.session_state.proficiency}")

    tab_lesson, tab_vocab, tab_grammar = st.tabs(["📘 Lesson Generator", "📖 Quick Vocabulary", "🧠 Grammar Tip"])

    with tab_lesson:
        left, right = st.columns([1, 1])
        with left:
            level = st.selectbox(
                "Level", PROFICIENCY_LEVELS,
                index=PROFICIENCY_LEVELS.index(st.session_state.proficiency),
            )
            topic = st.text_input("Daily-life topic", "Introducing yourself")
            if st.button("✨ Generate lesson", type="primary", use_container_width=True):
                with st.spinner("Building your lesson..."):
                    result = lesson_plan(source, target, level, topic)
                show_ai_result(result)
                if not str(result).startswith("AI service error:"):
                    st.session_state.lessons += 1
        with right:
            feature("Learning path", "🧭", "Daily conversation → Vocabulary → Grammar → Pronunciation → Listening → Speaking → Review")

    with tab_vocab:
        word = st.text_input("Word or phrase to learn right now", key="learn_vocab_word")
        if st.button("Explain word", key="learn_vocab_btn") and word.strip():
            with st.spinner("Building your word card..."):
                show_ai_result(explain_word(word, source, target))

    with tab_grammar:
        topic2 = st.text_input("Grammar topic", "Present simple tense", key="learn_grammar_topic")
        if st.button("Quick grammar tip", key="learn_grammar_btn"):
            with st.spinner("Preparing a quick tip..."):
                show_ai_result(ai_tutor(
                    f"Give one short, high-value tip about {topic2}, with one example.",
                    source, target, level=st.session_state.proficiency,
                ))

elif page == "Voice Translator":
    st.markdown('<div class="voice-title">🎙️ Voice Translator</div><div class="voice-sub">Speak clearly. See words instantly. Get a fast, accurate answer.</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    with a: st.markdown(f'<div class="card"><b>🎤 From</b><div style="font-size:18px;margin-top:5px">{name_of(source)}</div></div>', unsafe_allow_html=True)
    with b: st.markdown(f'<div class="card"><b>🌐 To</b><div style="font-size:18px;margin-top:5px">{name_of(target)}</div></div>', unsafe_allow_html=True)

    sw1, sw2 = st.columns(2)
    with sw1: voice_female = st.toggle("🔊 Female voice", value=st.session_state.prefer_female, key="vt_female")
    with sw2: fast_mode = st.toggle("🚀 Fast answer", value=True, key="vt_fast",
                                     help="On: one quick translation. Off: adds a grammar-correction pass.")

    # ---- Single, unified voice-recognition panel (Gemini 3.5 Transcribe) ----
    st.markdown(
        f'<div class="voice-studio">'
        f'<div class="voice-studio-head">'
        f'<span class="vs-dot"></span><span class="vs-name">AI Voice Recognition</span>'
        f'<span class="vs-tag">Gemini 3.5 Transcribe</span></div>'
        f'<div class="mic-stage"><div class="mic-orb"><div class="r1"></div><div class="r2"></div>'
        f'<div class="core">{MIC_SVG}</div></div>'
        f'<div class="mic-caption">One tap, real microphone, studio-grade transcription</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    audio = st.audio_input("🎤 Record voice for AI analysis", label_visibility="collapsed")

    typed = st.text_area("Text", placeholder="…or type your sentence here", height=90, label_visibility="collapsed")

    if st.button("⚡ Get Fast Answer", type="primary", use_container_width=True):
        text = typed.strip()
        if not text and audio:
            with st.spinner("Transcribing with Gemini…"):
                try:
                    text = transcribe_audio(audio.getvalue(), code_of(source), mime_type=audio.type or "audio/wav")
                except Exception as exc:
                    st.error(f"AI service error: {exc}")
        if not text:
            st.warning("Speak or type something first.")
        else:
            with st.spinner("Generating answer…"):
                if fast_mode:
                    translation = translate_fast(text, source, target)
                    correction = None
                else:
                    translation = translate_text(text, source, target)
                    correction = correct_text(text, source)
            st.markdown('<div class="section-title">Your answer</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tt-result"><b>📝 You said</b><br>{text}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tt-result success"><b>⚡ Answer</b><br>{translation}</div>', unsafe_allow_html=True)
            if correction is not None:
                st.markdown(f'<div class="tt-result"><b>✍️ Correction</b><br>{correction}</div>', unsafe_allow_html=True)
            if not str(translation).startswith("AI service error:"):
                st.session_state.history.insert(0, {"source": text, "from": name_of(source), "to": name_of(target), "result": translation})
                st.session_state.last_translation = translation
    if st.session_state.get("last_translation"):
        st.markdown('<div class="section-title">🔊 Listen</div>', unsafe_allow_html=True)
        render_browser_tts(st.session_state.last_translation, code_of(target), "Female" if voice_female else "Male")

elif page == "AI Tutor":
    st.title("🤖 AI Tutor")
    st.caption(f"Ask naturally. Get examples. Practice immediately. · Level: {st.session_state.proficiency}")
    question = st.text_area("Your question", placeholder="Explain when to use the present simple in easy English...")
    if st.button("Ask Tutor", type="primary") and question.strip():
        with st.spinner("Your tutor is thinking..."):
            show_ai_result(ai_tutor(question, source, target, retrieve_context(question), level=st.session_state.proficiency))

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
    st.caption(f"Level: {st.session_state.proficiency}")
    topic = st.text_input("Grammar topic", "Present simple tense")
    if st.button("Explain grammar", type="primary"):
        with st.spinner("Preparing a simple explanation..."):
            show_ai_result(ai_tutor(
                f"Teach {topic} with simple rules, examples, common mistakes and a mini exercise.",
                source, target, retrieve_context(topic), level=st.session_state.proficiency,
            ))

elif page == "Quiz & Tests":
    st.title("🧪 Quiz Lab")
    st.caption(f"Level: {st.session_state.proficiency}")
    topic = st.text_input("Quiz topic", "Daily conversation")
    if st.button("Generate quiz", type="primary"):
        with st.spinner("Creating your quiz..."):
            st.session_state.quiz = generate_quiz(source, target, topic, level=st.session_state.proficiency)
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
    st.markdown(f'<div class="card"><h3>{name}</h3><p>Native: {name_of(source)}<br>Learning: {name_of(target)}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">🎯 Proficiency level</div>', unsafe_allow_html=True)
    st.caption("Drag to set your current level — the AI Tutor, Grammar Coach, Lessons and Quizzes all pitch content to this.")
    st.session_state.proficiency = st.select_slider(
        "Proficiency (CEFR)", options=PROFICIENCY_LEVELS,
        value=st.session_state.proficiency, label_visibility="collapsed",
    )

    st.toggle("Daily reminders", True, key="pref_reminders")
    st.toggle("Show pronunciation tips", True, key="pref_pronunciation")
    st.session_state.prefer_female = st.toggle("Prefer female voice when available", value=st.session_state.prefer_female, key="pref_female_voice")
    st.session_state.autoplay = st.toggle("Auto-play translation audio", value=st.session_state.autoplay, key="pref_autoplay")

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
        cols[3].metric("AI", "generateContent")
        st.subheader("Management")
        st.write("Users • Content • Languages • AI & RAG • Quizzes • Analytics • Reports • Settings")
    elif expected:
        st.info("Enter the configured admin password.")
    else:
        st.warning("Configure TONGUETIE_ADMIN_PASSWORD in Streamlit Secrets.")
