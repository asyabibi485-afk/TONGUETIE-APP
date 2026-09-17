"""TongueTie voice services: Gemini transcription + browser TTS.

Transcription uses gemini-3.5-transcribe through the standard
`generateContent` REST endpoint with the recording sent inline as base64
(no separate Files-API upload round trip needed for short mic clips), which
keeps recording -> text fast and uses the same stateless request pattern as
the rest of the app. This is the single, unified voice-recognition path —
there is no separate in-browser recognition fallback, so results are
consistent across every browser/device.
"""

from __future__ import annotations

import base64
import html
import json
from typing import Any

from gemini_service import API_BASE, _api_key, _setting, _json_request, _extract_text


def _transcribe_model() -> str:
    return (_setting("GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-transcribe") or "gemini-3.5-transcribe").strip()


def transcribe_audio(audio_bytes: bytes, language_code: str = "", mime_type: str = "audio/wav") -> str:
    """Transcribe a recorded clip with Gemini 3.5 Transcribe.

    `language_code` is an optional hint (e.g. "en", "ur"); pass "" to let the
    model auto-detect the spoken language.
    """
    if not audio_bytes:
        return ""

    model = _transcribe_model()
    encoded = base64.b64encode(audio_bytes).decode("ascii")

    audio_config: dict[str, Any] = {"mode": "smart"}
    code = (language_code or "").strip()
    if code and "_" not in code and len(code) <= 20:
        audio_config["languageCodes"] = [code]

    payload = {
        "contents": [{
            "role": "user",
            "parts": [{"inline_data": {"mime_type": mime_type, "data": encoded}}],
        }],
        "generationConfig": {"audioTranscriptionConfig": audio_config},
    }

    url = f"{API_BASE}/models/{model}:generateContent"
    try:
        obj = _json_request(url, payload, timeout=120)
    except Exception as exc:
        raise RuntimeError(f"Speech analysis failed: {exc}") from exc

    text = _extract_text(obj)
    if not text:
        raise RuntimeError("Gemini returned no speech transcript. Try recording again.")
    return text


def render_browser_tts(text, language_code, voice_gender="Female"):
    """Render a small browser speech-synthesis player with a best-effort
    female/male voice preference (actual voices depend on the visitor's OS
    and browser)."""
    try:
        from streamlit.components.v1 import html as st_html
    except Exception:
        return

    safe_lang = html.escape(language_code or "en")
    gender = html.escape(voice_gender or "Female")
    aliases = {
        "zh": "zh-CN", "yue": "zh-HK", "he": "he-IL", "pt": "pt-BR",
        "nb": "nb-NO", "fil": "fil-PH", "jw": "jv-ID", "ckb": "ckb-IQ", "prs": "fa-AF",
    }
    browser_lang = aliases.get(language_code, language_code)

    markup = f"""
<!doctype html><html><head><meta charset='utf-8'><style>
body{{margin:0;background:transparent;font-family:Inter,Arial,sans-serif;color:#f8f9ff}}
.wrap{{display:flex;align-items:center;gap:10px;background:linear-gradient(135deg,#111a38,#17122d);
border:1px solid #34436f;border-radius:18px;padding:12px 14px;box-shadow:0 10px 30px rgba(0,0,0,.22)}}
button{{border:0;background:linear-gradient(90deg,#286c99,#7040c9);color:white;border-radius:12px;
padding:10px 16px;font-weight:700;cursor:pointer;transition:transform .15s}}
button:hover{{transform:translateY(-1px) scale(1.03)}}
small{{color:#aab4d1}}
</style></head><body><div class='wrap'>
<button id='play'>&#9654; Play</button><button id='stop'>&#9632; Stop</button>
<small>{gender} voice preference &middot; {html.escape(browser_lang)}</small></div>
<script>
const text={json.dumps(text or '')}; const lang={json.dumps(browser_lang)}; const gender={json.dumps(voice_gender)};
function pickVoice(){{const voices=speechSynthesis.getVoices();const base=lang.toLowerCase().split('-')[0];
const pool=voices.filter(v=>(v.lang||'').toLowerCase().startsWith(base));const list=pool.length?pool:voices;
if(gender.toLowerCase().startsWith('browser'))return list[0]||null;
const hints=gender.toLowerCase().startsWith('female')?['female','zira','samantha','aria','jenny','sara','susan','hazel']:['male','david','mark','guy','daniel','george'];
return list.find(v=>hints.some(h=>v.name.toLowerCase().includes(h)))||list[0]||null;}}
function play(){{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=lang;const v=pickVoice();
if(v)u.voice=v;u.rate=.94;u.pitch=gender.toLowerCase().startsWith('female')?1.05:.95;speechSynthesis.speak(u)}}
document.getElementById('play').onclick=play;document.getElementById('stop').onclick=()=>speechSynthesis.cancel();
</script></body></html>"""
    st_html(markup, height=64, scrolling=False)
