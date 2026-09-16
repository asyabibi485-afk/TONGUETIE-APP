"""TongueTie voice services.

STT: Gemini's dedicated transcription model.
TTS: browser SpeechSynthesis, with a best-effort female/male voice preference.
The browser approach requires no extra TTS API key and works inside Streamlit.
"""
import html
import os
import tempfile
from pathlib import Path

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

def transcribe_audio(audio_bytes, language_code):
    """Transcribe WAV bytes using Gemini's dedicated transcription model."""
    if not audio_bytes:
        return ""

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError(
            "google-genai is not installed. Reboot Streamlit after deploying "
            "the updated requirements.txt."
        ) from exc

    api_key = _setting("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured in Streamlit Secrets."
        )

    model = _setting("GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-transcribe")
    client = genai.Client(api_key=api_key)

    # Gemini Files API accepts a filesystem path, so save the Streamlit
    # UploadedFile bytes to a temporary WAV first.
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        path = tmp.name

    try:
        audio_file = client.files.upload(file=path)
        interaction = client.interactions.create(
            model=model,
            input=[{
                "type": "audio",
                "uri": audio_file.uri,
                "mime_type": audio_file.mime_type or "audio/wav",
            }],
        )
        text = getattr(interaction, "output_text", None)
        if not text:
            text = str(interaction)
        return text.strip()
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass

def render_browser_tts(text, language_code, voice_gender="Female"):
    """Render a browser speech-synthesis player inside Streamlit."""
    try:
        from streamlit.components.v1 import html as st_html
    except Exception:
        return

    safe_text = html.escape(text or "")
    safe_lang = html.escape(language_code or "en")
    gender = html.escape(voice_gender or "Female")

    # Browser locale aliases improve matching for some languages.
    aliases = {
        "zh": "zh-CN", "yue": "zh-HK", "he": "he-IL",
        "pt": "pt-BR", "nb": "nb-NO", "fil": "fil-PH",
        "jw": "jv-ID", "ckb": "ckb-IQ", "prs": "fa-AF",
    }
    browser_lang = aliases.get(language_code, language_code)

    markup = f"""
<!doctype html>
<html><head><meta charset="utf-8">
<style>
body{{margin:0;background:transparent;font-family:Arial,sans-serif;color:#f8f9ff}}
.wrap{{background:#10172d;border:1px solid #293761;border-radius:16px;padding:12px}}
button{{border:1px solid #44578e;background:linear-gradient(90deg,#286c99,#6340a5);
color:white;border-radius:12px;padding:10px 16px;font-weight:700;margin-right:7px}}
small{{color:#aab4d1}}
</style></head>
<body>
<div class="wrap">
<button id="play">▶ Play</button>
<button id="stop">■ Stop</button>
<small>{gender} voice preference · {browser_lang}</small>
</div>
<script>
const text = {safe_text!r};
const lang = {browser_lang!r};
const gender = {gender!r};
let utterance = null;

function pickVoice() {{
  const voices = speechSynthesis.getVoices();
  const sameLang = voices.filter(v => (v.lang || '').toLowerCase().startsWith(lang.toLowerCase().split('-')[0]));
  const pool = sameLang.length ? sameLang : voices;
  const femaleHints = ['female','zira','samantha','aria','jenny','sara','susan','hazel','google uk english female'];
  const maleHints = ['male','david','mark','guy','daniel','george'];
  const hints = gender.toLowerCase().startsWith('female') ? femaleHints : maleHints;
  if (gender.toLowerCase().includes('browser')) return pool[0] || null;
  return pool.find(v => hints.some(h => v.name.toLowerCase().includes(h))) || pool[0] || null;
}}

function play() {{
  speechSynthesis.cancel();
  utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang;
  const voice = pickVoice();
  if (voice) utterance.voice = voice;
  utterance.rate = 0.92;
  utterance.pitch = gender.toLowerCase().startsWith('female') ? 1.05 : 0.95;
  speechSynthesis.speak(utterance);
}}
document.getElementById('play').onclick = play;
document.getElementById('stop').onclick = () => speechSynthesis.cancel();
speechSynthesis.onvoiceschanged = () => {{}};
</script></body></html>
"""
    st_html(markup, height=76, scrolling=False)
