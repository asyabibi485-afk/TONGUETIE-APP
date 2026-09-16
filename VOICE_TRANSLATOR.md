# TongueTie real Voice Translator

The previous app showed a placeholder because `speech_service.py` raised
`NotImplementedError`.

This version now provides:

1. Streamlit microphone recording via `st.audio_input`.
2. Real speech-to-text through Gemini's `gemini-3.5-transcribe` model.
3. Translation with TongueTie's Gemini translator.
4. Grammar/error correction of the spoken transcript.
5. Browser voice playback with Female/Male/Browser-default preference.

Streamlit's audio widget supplies a WAV recording at a speech-friendly sample
rate, and Gemini's transcription API accepts uploaded audio for transcription.

## Streamlit Secrets

```toml
GEMINI_API_KEY = "your-real-key"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TRANSCRIBE_MODEL = "gemini-3.5-transcribe"
TONGUETIE_ADMIN_PASSWORD = "your-admin-password"
```

The female voice preference is best-effort because the browser SpeechSynthesis
API does not provide a standard cross-browser gender field. The app first
prefers voices whose names commonly indicate a female voice for the requested
language and falls back to an available voice.

No TTS API key is required for browser playback.
