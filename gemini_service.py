
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
    """Send a Gemini request without reusing a client across Streamlit reruns."""
    key = _setting("GEMINI_API_KEY")
    if not key:
        return "AI service error: GEMINI_API_KEY is not configured in Streamlit Secrets."

    try:
        from google import genai
    except ImportError:
        return "AI service error: google-genai is missing. Reboot Streamlit after deploying requirements.txt."

    client = None
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=_model(),
            contents=prompt,
        )
        result = getattr(response, "text", None)
        return result.strip() if result else str(response)
    except Exception as e:
        msg = str(e)
        # A stale/closed SDK client must not be surfaced as the normal user error.
        # Retry once with a completely new client.
        if "client has been closed" in msg.lower() or "closed" in msg.lower():
            try:
                fresh = genai.Client(api_key=key)
                response = fresh.models.generate_content(model=_model(), contents=prompt)
                result = getattr(response, "text", None)
                return result.strip() if result else str(response)
            except Exception as retry_error:
                return f"AI service error: {retry_error}"
            finally:
                try:
                    fresh.close()
                except Exception:
                    pass
        return f"AI service error: {msg}"
    finally:
        try:
            if client is not None:
                client.close()
        except Exception:
            pass

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
