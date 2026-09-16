"""TongueTie voice services using Gemini REST APIs and browser TTS.

No persistent Google SDK client is used. Audio is uploaded with the Gemini
Files REST API and transcribed through the Interactions API.
"""

from __future__ import annotations

import html
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
import tempfile
from typing import Any

from gemini_service import _api_key, _setting


API_BASE = "https://generativelanguage.googleapis.com/v1beta"
UPLOAD_BASE = "https://generativelanguage.googleapis.com/upload/v1beta"


def _response_json(response) -> dict[str, Any]:
    return json.loads(response.read().decode("utf-8"))


def _error_text(raw: str, status: int | None = None) -> str:
    try:
        obj = json.loads(raw)
        message = obj.get("error", {}).get("message")
        if message:
            return f"Gemini API error ({status}): {message}" if status else f"Gemini API error: {message}"
    except Exception:
        pass
    return f"Gemini API error ({status}): {' '.join(raw.split()) or 'Unknown error'}"


def _upload_audio(path: str, mime_type: str) -> str:
    size = os.path.getsize(path)
    display_name = os.path.basename(path) or "tonguetie-audio.wav"

    start_request = urllib.request.Request(
        f"{UPLOAD_BASE}/files",
        data=json.dumps({"file": {"display_name": display_name}}).encode("utf-8"),
        headers={
            "x-goog-api-key": _api_key(),
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(start_request, timeout=30) as response:
            upload_url = response.headers.get("x-goog-upload-url")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(_error_text(raw, exc.code)) from exc
    except Exception as exc:
        raise RuntimeError(f"Audio upload initialization failed: {exc}") from exc

    if not upload_url:
        raise RuntimeError("Gemini did not return an upload URL for the recording.")

    with open(path, "rb") as fh:
        audio = fh.read()

    upload_request = urllib.request.Request(
        upload_url,
        data=audio,
        headers={
            "Content-Length": str(len(audio)),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
            "Content-Type": mime_type,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(upload_request, timeout=90) as response:
            result = _response_json(response)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(_error_text(raw, exc.code)) from exc
    except Exception as exc:
        raise RuntimeError(f"Audio upload failed: {exc}") from exc

    file_obj = result.get("file") or result
    uri = file_obj.get("uri") if isinstance(file_obj, dict) else None
    if not uri:
        raise RuntimeError("Gemini uploaded the recording but returned no file URI.")
    return uri


def _extract_transcript(obj: dict[str, Any]) -> str:
    direct = obj.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    pieces: list[str] = []
    for output in obj.get("outputs") or []:
        if not isinstance(output, dict):
            continue
        text = output.get("text")
        if isinstance(text, str) and text.strip():
            pieces.append(text)
        for part in output.get("content") or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                pieces.append(part["text"])
    return "\n".join(pieces).strip()


def transcribe_audio(audio_bytes: bytes, language_code: str = "") -> str:
    """Transcribe a Streamlit audio_input recording with Gemini 3.5 Transcribe."""
    if not audio_bytes:
        return ""

    model = (_setting("GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-transcribe") or "gemini-3.5-transcribe").strip()
    code = (language_code or "").strip()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        path = tmp.name

    try:
        file_uri = _upload_audio(path, "audio/wav")
        config = {"mode": "smart"}
        if code and "_" not in code and len(code) <= 20:
            config["language_codes"] = [code]

        payload = {
            "model": model,
            "input": [{
                "type": "audio",
                "uri": file_uri,
                "mime_type": "audio/wav",
            }],
            "generation_config": {"transcription_config": config},
        }
        request = urllib.request.Request(
            f"{API_BASE}/interactions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": _api_key(),
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            obj = _response_json(response)
        text = _extract_transcript(obj)
        if not text:
            raise RuntimeError("Gemini returned no speech transcript.")
        return text
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(_error_text(raw, exc.code)) from exc
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"Speech analysis failed: {exc}") from exc
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass


def render_browser_tts(text, language_code, voice_gender="Female"):
    """Render browser speech synthesis with a best-effort voice preference."""
    try:
        from streamlit.components.v1 import html as st_html
    except Exception:
        return

    safe_text = html.escape(text or "")
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
.wrap{{background:linear-gradient(135deg,#111a38,#17122d);border:1px solid #34436f;border-radius:18px;padding:12px;box-shadow:0 10px 30px rgba(0,0,0,.22)}}
button{{border:0;background:linear-gradient(90deg,#286c99,#7040c9);color:white;border-radius:12px;padding:10px 16px;font-weight:700;margin-right:7px}}
small{{color:#aab4d1}}
</style></head><body><div class='wrap'>
<button id='play'>▶ Play</button><button id='stop'>■ Stop</button>
<small>{gender} preference · {browser_lang}</small></div>
<script>
const text={json.dumps(text or '')}; const lang={json.dumps(browser_lang)}; const gender={json.dumps(voice_gender)};
function pickVoice(){{const voices=speechSynthesis.getVoices();const base=lang.toLowerCase().split('-')[0];const pool=voices.filter(v=>(v.lang||'').toLowerCase().startsWith(base));const list=pool.length?pool:voices;if(gender.toLowerCase().startsWith('browser'))return list[0]||null;const hints=gender.toLowerCase().startsWith('female')?['female','zira','samantha','aria','jenny','sara','susan','hazel']:['male','david','mark','guy','daniel','george'];return list.find(v=>hints.some(h=>v.name.toLowerCase().includes(h)))||list[0]||null;}}
function play(){{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang=lang;const v=pickVoice();if(v)u.voice=v;u.rate=.92;u.pitch=gender.toLowerCase().startsWith('female')?1.05:.95;speechSynthesis.speak(u)}}
document.getElementById('play').onclick=play;document.getElementById('stop').onclick=()=>speechSynthesis.cancel();
</script></body></html>"""
    st_html(markup, height=76, scrolling=False)
