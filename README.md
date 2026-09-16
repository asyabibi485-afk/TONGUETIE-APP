# TongueTie 🌍🗣️

**Learn Languages. Speak Confidently. Understand the World.**

A creative, mobile-friendly Streamlit language-learning app with Gemini-powered translation, correction, tutoring, vocabulary, grammar, quizzes, RAG knowledge, and voice transcription/TTS.

## Features

- 100+ language-ready language selector
- Voice Translator: microphone/audio → transcription → translation → correction → browser voice playback
- AI Tutor with knowledge-base (RAG) context
- Correct My English
- Vocabulary and difficult-word explanations
- Grammar learning
- Lessons and quizzes/tests
- Progress and profile screens
- Separate Admin screen
- Responsive dark/glass mobile-style UI
- REST-based Gemini integration to avoid persistent SDK client lifecycle errors

## GitHub repository structure

```text
app.py
gemini_service.py
speech_service.py
language_data.py
rag.py
requirements.txt
 data/knowledge_base.txt
 .streamlit/secrets.toml.example
 assets/
 prototype/
```

## Run locally

1. Install Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example` and add your Gemini API key.
4. Start the app:

```bash
streamlit run app.py
```

## Streamlit Cloud

1. Upload **all files in this repository directly to the GitHub repository root**.
2. In Streamlit Cloud, select `app.py` as the main file.
3. Add the values from `.streamlit/secrets.toml.example` under **App settings → Secrets**.
4. Save/reboot the app.

Never commit a real API key or real admin password to GitHub.

See `STREAMLIT_CLOUD_DEPLOY.md` and `DEPLOY_FIX.md` for deployment notes.

## Gemini configuration

The app uses REST requests rather than a long-lived `google-genai` client.

Required:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Optional model settings are documented in `.streamlit/secrets.toml.example`.

## Voice transcription

The voice flow uses the Gemini Files REST upload flow and the Gemini transcription interaction. Browser speech synthesis is used for playback; available voices depend on the user's browser/device and language.

## Security

- Do not commit `.streamlit/secrets.toml`.
- Do not put API keys in `app.py`, JavaScript, or Git history.
- Replace the example admin password with a secret stored in Streamlit Secrets.
