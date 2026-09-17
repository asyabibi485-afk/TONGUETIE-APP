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

Language coverage (250+ languages/locales across every populated
continent), the RAG knowledge base, lesson/quiz/vocabulary/grammar
generation, and the Streamlit Cloud deployment flow are unchanged.

## Front-page redesign + single voice-recognition path

- Removed the sidebar entirely — language pickers now live in a
  front-and-center "front controls" panel, and primary navigation is a
  5-tab row plus a "More tools" dropdown for the rest, both styled as one
  continuous glass "dock."
- Removed the separate in-browser live-recognition preview. There is now
  **one** voice-recognition path — the AI-powered recorder
  (`st.audio_input` → `gemini-3.5-transcribe`) — styled as a dedicated
  "Voice Studio" panel with a pulsing mic centerpiece, so behavior is
  consistent across every browser/device instead of depending on
  Web-Speech-API support.
- The recorder now sends the browser's actual recorded MIME type to
  Gemini instead of assuming WAV.
- The "Fast answer" toggle on the Voice Translator page is now wired up:
  on, it does one quick translation; off, it also runs a grammar
  correction pass.

## Faster "Get Fast Answer"

The fast path was still asking Gemini for a translation *plus* a learning
note, and output length is the main lever on response time for flash
models. Added `translate_fast()` in `gemini_service.py`: translation-only
prompt, `maxOutputTokens` capped at 300, lower temperature. The "🚀 Fast
answer" toggle now calls this instead of the full `translate_text()` +
`correct_text()` pair, which are still used when that toggle is off.

## Broader language coverage + proficiency-aware, faster AI everywhere

- Expanded the language list from 143 to **252** entries — added many more
  African, Pacific, Central Asian, Caucasus, Indigenous American and
  Southeast Asian languages so most learners will find their target
  language, not just the largest world languages.
- Added a **proficiency slider** (real `st.select_slider`, CEFR A1–C2) on
  the Profile page. It's now the single source of truth for level, and
  feeds into the AI Tutor, Grammar Coach, Quiz generator and Lesson
  generator, so content is pitched at the right difficulty instead of a
  generic default.
- The Learning Studio now uses real **`st.tabs`** (Lesson Generator / Quick
  Vocabulary / Grammar Tip) instead of one long page.
- App-wide response speed: every AI call now caps output length
  (`maxOutputTokens`), not just the Voice Translator's fast path — output
  length is the main latency lever for flash models, so this makes AI
  Tutor, Grammar, Vocabulary, Quiz and Lessons noticeably snappier too.

## Faster Vocabulary Builder + Correct My English

`explain_word()` and `correct_text()` were still asking for long,
multi-section answers with no token cap, which is why Vocabulary Builder in
particular could feel stuck. Both are now concise, single-pass prompts with
a tight `maxOutputTokens` cap (350 / 500) — trimmed content, not skipped
content: word cards keep meaning, part of speech, pronunciation, one
example and one common mistake; corrections keep all four sections, just
written more concisely.
