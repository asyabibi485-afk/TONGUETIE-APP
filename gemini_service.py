
import os
def _setting(name, default=None):
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return default

def _client():
    key = _setting("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured in Streamlit Secrets or environment variables."
        )
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed. Add google-genai to requirements.txt "
            "and reboot the Streamlit app."
        ) from exc
    return genai.Client(api_key=key)

def _model():
    # Set GEMINI_MODEL in Streamlit Secrets to a model enabled for your API account.
    return _setting("GEMINI_MODEL", "gemini-2.5-flash")

def ask(prompt):
    try:
        response = _client().models.generate_content(model=_model(), contents=prompt)
        return getattr(response, "text", None) or str(response)
    except Exception as e:
        return f"AI service error: {e}"

def ai_tutor(question, source, target, context=""):
    return ask(f"""You are TongueTie, a multilingual language tutor.
Learner's first language: {source}
Target language: {target}
Question: {question}
Relevant learning context:
{context}
Answer clearly. If useful, give examples, common mistakes, a mini exercise, and an English/learner-language explanation. Do not pretend to have heard audio unless a transcript is supplied.""")

def translate_text(text, source, target):
    return ask(f"""Translate the following text from {source} to {target}.
Preserve meaning and natural register.
Return:
1. Natural translation
2. Literal/learning note when useful
3. Romanization only when the target script normally needs it for learners
Text: {text}""")

def correct_text(text, language):
    return ask(f"""Correct this {language} text for a learner.
Return:
- Corrected version
- What was wrong
- Why
- A more natural alternative when appropriate
Text: {text}""")

def explain_word(word, source, target):
    return ask(f"""Teach the word/phrase "{word}" for someone who speaks {source} and is learning {target}.
Include meaning, part of speech, pronunciation guidance, examples, common mistakes, synonyms/related words, and a short practice question.""")

def generate_quiz(source, target, topic):
    return ask(f"""Create a 10-question language-learning quiz for {target}, explained for a {source}-speaking learner.
Topic: {topic}
Include multiple choice questions and an answer key at the end.""")

def lesson_plan(source, target, level, topic):
    return ask(f"""Create a practical 10-minute {target} lesson for a {source}-speaking learner.
Level: {level}
Topic: {topic}
Include dialogue, vocabulary, grammar point, pronunciation focus, comprehension check, speaking task and review.""")
