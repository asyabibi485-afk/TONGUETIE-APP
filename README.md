# TongueTie 🌍🗣️

**Learn Languages. Speak Confidently. Understand the World.**

A creative, mobile-friendly Streamlit language-learning app with Gemini-powered
translation, correction, tutoring, vocabulary, grammar, quizzes, RAG knowledge,
and real voice recognition + transcription/TTS.

## Features

- 130+ language-ready language selector (every populated continent, incl.
  Urdu, Arabic, Persian, Chinese, Hindi, Swahili, Quechua and more)
- **Voice Translator**: real microphone recording → AI transcription →
  translation → correction → browser voice playback
- **Live browser voice recognition** preview panel with an animated waveform
  (runs client-side, Chrome/Edge)
- AI Tutor with knowledge-base (RAG) context
- Correct My English
- Vocabulary and difficult-word explanations
- Grammar learning
- Lessons and quizzes/tests
- Progress and profile screens with toggle-switch preferences
- Separate password-gated Admin screen
- Always-visible pill tab-bar navigation + drag-to-reorder quick-language
  chips
- Responsive dark/glass UI with animated gradient accents
- Stateless REST calls to the current Gemini `generateContent` API (no
  cached SDK client, so Streamlit reruns can't hit a closed-client error)

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

Upload **all files in this repository directly to the GitHub repository
root** — `app.py` and the other `.py` modules must sit beside each other,
not inside a subfolder.

## Run locally

1. Install Python 3.10+.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example`
   and add your real Gemini API key.
4. Start the app:

   ```bash
   streamlit run app.py
   ```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub (all files at the repo root — see the
   structure above).
2. Go to [share.streamlit.io](https://share.streamlit.io), click **New app**,
   and pick your repo/branch.
3. Set **Main file path** to `app.py`.
4. Open **App settings → Secrets** and paste the contents of
   `.streamlit/secrets.toml.example`, filled in with your real values:

   ```toml
   GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
   GEMINI_MODEL = "gemini-flash-latest"
   GEMINI_FALLBACK_MODELS = "gemini-3.8-flash,gemini-3.6-flash,gemini-2.5-flash"
   GEMINI_TRANSCRIBE_MODEL = "gemini-3.5-transcribe"
   TONGUETIE_ADMIN_PASSWORD = "choose-a-real-password"
   ```

5. Click **Deploy**, then **Reboot app** any time you change Secrets.

Get a Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

Never commit a real API key or real admin password to GitHub — only
`.streamlit/secrets.toml.example` (with placeholder values) belongs in the
repo; the real `.streamlit/secrets.toml` is already listed in `.gitignore`.

## Gemini configuration

The app uses stateless REST requests to the standard `generateContent`
endpoint rather than a long-lived SDK client — see `UPGRADE_NOTES.md` for
details on why, and what changed from earlier builds of this repo.

Required secret:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Optional model overrides are documented in `.streamlit/secrets.toml.example`.
If your API key doesn't have access to the primary model, the app
automatically retries the fallback models in order.

## Voice features

- **Recorder (AI-powered)**: `st.audio_input` captures real microphone audio
  in the browser; `speech_service.transcribe_audio` sends it to
  `gemini-3.5-transcribe` for transcription, which then feeds translation
  and correction.
- **Live preview (browser-only)**: a Web Speech API panel shows words as you
  speak, for an instant, no-server-round-trip preview. Availability depends
  on the visitor's browser (best in Chrome/Edge).
- **Playback**: browser `SpeechSynthesis`; available voices and languages
  depend on the visitor's OS/browser. No extra TTS API key required.

## Security

- Do not commit `.streamlit/secrets.toml`.
- Do not put API keys in `app.py`, JavaScript, or Git history.
- Replace the example admin password with a real secret stored in Streamlit
  Secrets.
