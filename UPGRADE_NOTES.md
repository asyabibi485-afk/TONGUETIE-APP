# UI + reliability upgrade

This pass fixes the AI backend and redesigns the interface. If you're
comparing against an older copy of this repo, here's what changed.

## Fixed: the AI calls were broken

The previous build called a non-standard `/v1beta/interactions` path with a
made-up request shape. Real Gemini API calls now go through the documented,
stable REST endpoint:

```
POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
```

- `gemini_service.py` — text (tutor, translate, correct, quiz, lessons) now
  uses `generateContent` with the standard `contents[].parts[]` request body
  and `candidates[].content.parts[].text` response shape. It still opens a
  fresh stateless request per call (no cached SDK client), so it keeps the
  original fix for Streamlit's "client has been closed" rerun bug.
- `speech_service.py` — transcription uses `gemini-3.5-transcribe` through
  the same `generateContent` endpoint, sending the recording inline as
  base64 (no separate Files-API upload round trip needed for short mic
  clips), which is both simpler and faster.
- Model names in `.streamlit/secrets.toml.example` were updated to models
  that are current as of this build (`gemini-flash-latest`, with
  `gemini-3.8-flash` / `gemini-3.6-flash` / `gemini-2.5-flash` as automatic
  fallbacks if your API key doesn't have access to the primary one).

## Redesigned interface

- **Visible, "real" microphone** — the Voice Translator page has a large
  animated mic centerpiece (pulsing glow rings) wrapping Streamlit's native
  `st.audio_input` recorder, which asks for real microphone permission and
  records real audio in the browser.
- **Always-visible navigation ("side tab" in front)** — instead of hiding
  pages behind the sidebar hamburger on mobile, the app now has a pill-style
  tab bar pinned at the top of the main content, plus a language/settings
  panel in the sidebar.
- **Switches** — settings (auto-play audio, preferred voice gender, live
  recognition preview, reminders, pronunciation tips) are all toggle
  switches (`st.toggle`) styled with the app's gradient accent.
- **Movable elements** — feature/result cards lift and glow on hover, and
  the sidebar's "Quick languages" chips are drag-and-drop reorderable
  (saved in the browser for that device).
- **Live voice recognition** — a new browser-based speech-recognition panel
  (`render_live_recognition` in `speech_service.py`) shows words appear in
  real time as you speak, with its own animated waveform, purely
  client-side (Chrome/Edge). It's a fast preview that sits alongside the
  AI-powered recorder, which remains the path used for translation.

## Everything else

Language coverage (130+ languages/locales across every populated
continent), the RAG knowledge base, lesson/quiz/vocabulary/grammar
generation, and the Streamlit Cloud deployment flow are unchanged.
