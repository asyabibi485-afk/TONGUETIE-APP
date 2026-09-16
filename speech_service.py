"""TongueTie voice services: Gemini transcription + browser TTS + a live
in-browser speech-recognition preview widget.

Transcription uses gemini-3.5-transcribe through the standard
`generateContent` REST endpoint with the recording sent inline as base64
(no separate Files-API upload round trip needed for short mic clips), which
keeps recording -> text fast and uses the same stateless request pattern as
the rest of the app.
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


_RECOGNITION_LANG_ALIASES = {
    "zh": "zh-CN", "yue": "zh-HK", "he": "he-IL", "pt": "pt-BR", "nb": "nb-NO",
    "fil": "fil-PH", "jw": "jv-ID", "ar": "ar-SA", "es": "es-ES", "fr": "fr-FR",
    "de": "de-DE", "en": "en-US",
}


def render_live_recognition(language_code: str, height: int = 300):
    """A self-contained, real-time browser speech-recognition preview.

    Uses the Web Speech API (Chrome/Edge) to show words appear live as the
    visitor speaks, with a running waveform driven by the actual microphone
    input. This is a fast, client-side preview; it does not use the Gemini
    API and does not require the server round trip. Availability depends on
    the visitor's browser (Safari/Firefox support is limited).
    """
    try:
        from streamlit.components.v1 import html as st_html
    except Exception:
        return

    bcp47 = _RECOGNITION_LANG_ALIASES.get(language_code, language_code or "en-US")
    if "-" not in bcp47:
        bcp47 = f"{bcp47}-{bcp47.upper()}" if len(bcp47) == 2 else bcp47

    markup = f"""
<!doctype html><html><head><meta charset='utf-8'><style>
*{{box-sizing:border-box}}
body{{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif;color:#f8f9ff}}
.panel{{border:1px solid #293761;border-radius:22px;background:linear-gradient(160deg,rgba(16,23,45,.92),rgba(21,29,56,.92));
padding:18px;box-shadow:0 16px 40px rgba(0,0,0,.28)}}
.row{{display:flex;align-items:center;gap:12px;justify-content:space-between;flex-wrap:wrap}}
.title{{font-weight:800;font-size:15px}}
.status{{font-size:12px;color:#aab4d1;padding:5px 10px;border-radius:999px;border:1px solid #33456f;background:#0f1730}}
.status.live{{color:#57f0b0;border-color:#2c8f6c}}
.mic-wrap{{position:relative;width:92px;height:92px;margin:14px auto 6px;display:flex;align-items:center;justify-content:center}}
.ring{{position:absolute;inset:0;border-radius:50%;background:radial-gradient(circle,rgba(85,199,255,.35),transparent 70%);
opacity:0;transition:opacity .2s}}
.ring.on{{opacity:1;animation:pulse 1.1s ease-in-out infinite}}
@keyframes pulse{{0%{{transform:scale(.85)}}50%{{transform:scale(1.18)}}100%{{transform:scale(.85)}}}}
.mic-btn{{position:relative;width:64px;height:64px;border-radius:50%;border:0;cursor:pointer;
background:linear-gradient(135deg,#55c7ff,#9b5cff);display:flex;align-items:center;justify-content:center;
box-shadow:0 10px 26px rgba(122,90,255,.45);transition:transform .15s}}
.mic-btn:hover{{transform:scale(1.05)}}
.mic-btn.active{{background:linear-gradient(135deg,#ff6b8b,#ff3d6b)}}
.mic-btn svg{{width:26px;height:26px;fill:#0a0e1c}}
.wave{{height:34px;display:flex;align-items:center;justify-content:center;gap:3px;margin-top:8px}}
.bar{{width:3px;height:6px;border-radius:4px;background:linear-gradient(#55c7ff,#9b5cff);transition:height .09s}}
.transcript{{min-height:64px;margin-top:12px;padding:12px 14px;border-radius:14px;background:#0d1428;
border:1px solid #253458;font-size:14px;line-height:1.5}}
.interim{{color:#8fa0d6}}
.actions{{display:flex;gap:8px;margin-top:10px}}
button.util{{border:1px solid #3a4d7d;background:#141d38;color:#e7ecff;border-radius:10px;padding:8px 12px;
font-size:12px;font-weight:700;cursor:pointer}}
button.util:hover{{border-color:#7de2ff}}
.hint{{font-size:11px;color:#7d8ab3;margin-top:8px}}
</style></head><body>
<div class="panel">
  <div class="row"><span class="title">&#9889; Live voice recognition</span><span id="status" class="status">Tap mic to start</span></div>
  <div class="mic-wrap"><div id="ring" class="ring"></div>
    <button id="mic" class="mic-btn" title="Start/stop listening">
      <svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z"/></svg>
    </button>
  </div>
  <div id="wave" class="wave"></div>
  <div id="transcript" class="transcript">Recognized speech will appear here as you talk&hellip;</div>
  <div class="actions">
    <button class="util" id="copyBtn">&#128203; Copy text</button>
    <button class="util" id="clearBtn">&#10227; Clear</button>
  </div>
  <div class="hint">Runs entirely in your browser (Chrome/Edge). Language: {html.escape(bcp47)}</div>
</div>
<script>
const wave = document.getElementById('wave');
for (let i=0;i<24;i++){{const b=document.createElement('div');b.className='bar';wave.appendChild(b);}}
const bars=[...wave.children];
const micBtn=document.getElementById('mic');
const ring=document.getElementById('ring');
const statusEl=document.getElementById('status');
const transcriptEl=document.getElementById('transcript');
let finalText='';
let listening=false;
let audioCtx, analyser, dataArray, rafId, stream;

async function startWave(){{
  try{{
    stream = await navigator.mediaDevices.getUserMedia({{audio:true}});
    audioCtx = new (window.AudioContext||window.webkitAudioContext)();
    const src = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    src.connect(analyser);
    dataArray = new Uint8Array(analyser.frequencyBinCount);
    drawWave();
  }}catch(e){{ /* mic permission declined; recognition may still work in some browsers */ }}
}}
function drawWave(){{
  if(!analyser) return;
  analyser.getByteFrequencyData(dataArray);
  bars.forEach((b,i)=>{{const v=dataArray[i % dataArray.length]||0; b.style.height=Math.max(6, (v/255)*34)+'px';}});
  rafId = requestAnimationFrame(drawWave);
}}
function stopWave(){{
  if(rafId) cancelAnimationFrame(rafId);
  if(stream) stream.getTracks().forEach(t=>t.stop());
  if(audioCtx) audioCtx.close().catch(()=>{{}});
  bars.forEach(b=>b.style.height='6px');
}}

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
if (SR){{
  recognition = new SR();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = {json.dumps(bcp47)};
  recognition.onresult = (event) => {{
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {{
      const t = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalText += t + ' ';
      else interim += t;
    }}
    transcriptEl.innerHTML = (finalText || '') + '<span class="interim">' + interim + '</span>';
  }};
  recognition.onerror = () => {{ statusEl.textContent = 'Recognition error - tap to retry'; }};
  recognition.onend = () => {{
    if (listening) {{ try {{ recognition.start(); }} catch(e){{}} }}
  }};
}}

micBtn.onclick = async () => {{
  if (!SR) {{
    statusEl.textContent = 'Not supported in this browser';
    return;
  }}
  if (!listening) {{
    listening = true;
    micBtn.classList.add('active');
    ring.classList.add('on');
    statusEl.textContent = 'Listening...';
    statusEl.classList.add('live');
    finalText = '';
    transcriptEl.textContent = '';
    try {{ recognition.start(); }} catch(e){{}}
    startWave();
  }} else {{
    listening = false;
    micBtn.classList.remove('active');
    ring.classList.remove('on');
    statusEl.textContent = 'Stopped';
    statusEl.classList.remove('live');
    try {{ recognition.stop(); }} catch(e){{}}
    stopWave();
  }}
}};
document.getElementById('copyBtn').onclick = () => {{
  const text = (finalText || transcriptEl.textContent || '').trim();
  if (!text) return;
  navigator.clipboard.writeText(text).then(()=>{{
    const btn = document.getElementById('copyBtn');
    const old = btn.textContent; btn.textContent = 'Copied!';
    setTimeout(()=>btn.textContent = old, 1200);
  }});
}};
document.getElementById('clearBtn').onclick = () => {{
  finalText=''; transcriptEl.textContent = 'Recognized speech will appear here as you talk\\u2026';
}};
if(!SR){{ statusEl.textContent = 'Browser not supported - use the recorder below'; }}
</script>
</body></html>"""
    st_html(markup, height=height, scrolling=False)
