"""TongueTie AI service client.

Stateless REST client for the Gemini API's standard `generateContent`
endpoint (POST /v1beta/models/{model}:generateContent).

Why REST-only, no SDK client?
- Streamlit reruns application code on every interaction.
- A long-lived SDK client object can go stale/closed between reruns and
  raise "Cannot send a request, as the client has been closed."
- This module opens a fresh short-lived HTTPS connection per request, with
  explicit timeout and bounded retry handling, and never caches a client.

This build intentionally uses the classic, fully-documented `generateContent`
REST surface (https://ai.google.dev/api) rather than the newer Interactions
API, since generateContent has a stable, well-specified request/response
shape and remains fully supported.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _setting(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return default


def _api_key() -> str:
    key = _setting("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to Streamlit Secrets "
            "(App settings -> Secrets) and reboot the app."
        )
    return key.strip()


def _model() -> str:
    return (_setting("GEMINI_MODEL", "gemini-flash-latest") or "gemini-flash-latest").strip()


def _models_to_try() -> list[str]:
    """Primary model plus a short list of current, known-good fallbacks.

    Google periodically retires model IDs. If the primary model name is
    unavailable to a given API key/project, we automatically retry with the
    next candidate instead of failing the whole request.
    """
    primary = _model()
    fallback_raw = _setting(
        "GEMINI_FALLBACK_MODELS",
        "gemini-3.8-flash,gemini-3.6-flash,gemini-2.5-flash",
    ) or ""
    models = [primary]
    for item in fallback_raw.split(","):
        item = item.strip()
        if item and item not in models:
            models.append(item)
    return models


def _json_request(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int = 90,
    retries: int = 2,
) -> dict[str, Any]:
    """POST JSON with bounded retry handling for transient failures."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-goog-api-key": _api_key(),
    }

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_error = exc
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            # Retry only temporary/server/rate-limit errors.
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt >= retries:
                raise RuntimeError(_api_error_message(detail, exc.code)) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt >= retries:
                raise RuntimeError(f"Network/AI response error: {exc}") from exc

        time.sleep(1.2 * (2**attempt))

    raise RuntimeError(f"AI request failed: {last_error}")


def _api_error_message(detail: str, status: int | None = None) -> str:
    try:
        parsed = json.loads(detail)
        error = parsed.get("error", {}) if isinstance(parsed, dict) else {}
        message = error.get("message") if isinstance(error, dict) else None
        if message:
            return f"Gemini API error ({status}): {message}" if status else f"Gemini API error: {message}"
    except Exception:
        pass
    cleaned = " ".join(detail.split())
    return f"Gemini API error ({status}): {cleaned or 'Unknown API error'}"


def _extract_text(obj: dict[str, Any]) -> str:
    pieces: list[str] = []
    for candidate in obj.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                pieces.append(part["text"])
    if pieces:
        return "\n".join(pieces).strip()

    prompt_feedback = obj.get("promptFeedback") or {}
    block_reason = prompt_feedback.get("blockReason")
    if block_reason:
        return f"AI service error: request blocked ({block_reason})."
    return ""


def generate(
    parts: list[dict[str, Any]],
    *,
    temperature: float = 0.4,
    generation_config_extra: dict[str, Any] | None = None,
    model_override: str | None = None,
    timeout: int = 90,
) -> str:
    """Low-level call to generateContent with one user turn made of `parts`.

    `parts` follows the Gemini `Part` schema, e.g. [{"text": "..."}] or
    [{"inline_data": {"mime_type": "...", "data": "<base64>"}}].
    """
    generation_config: dict[str, Any] = {"temperature": max(0.0, min(float(temperature), 1.0))}
    if generation_config_extra:
        generation_config.update(generation_config_extra)

    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": generation_config,
    }

    models = [model_override] if model_override else _models_to_try()
    last: Exception | None = None
    for model in models:
        url = f"{API_BASE}/models/{urllib.parse.quote(model, safe='')}:generateContent"
        try:
            result = _json_request(url, payload, timeout=timeout)
            text = _extract_text(result)
            if text and not text.startswith("AI service error:"):
                return text
            last = RuntimeError(text or "Gemini returned no text output.")
        except RuntimeError as exc:
            last = exc
            message = str(exc).lower()
            # Only fall through to the next model for availability-style errors.
            if not any(token in message for token in ("not found", "unsupported", "model", "404")):
                break

    return f"AI service error: {last or 'Unknown Gemini error.'}"


def ask(prompt: str, *, temperature: float = 0.4, max_tokens: int = 1024) -> str:
    """Send one stateless text request to Gemini.

    No SDK client is created, cached, closed, or reused. This directly avoids
    the Streamlit error: "Cannot send a request, as the client has been closed."

    `max_tokens` caps generation length — output length is the main lever on
    response latency for flash models, so every helper below keeps a
    reasonable cap instead of letting the model ramble, which keeps the app
    feeling responsive.
    """
    if not prompt or not prompt.strip():
        return "AI service error: empty prompt."
    return generate(
        [{"text": prompt.strip()}],
        temperature=temperature,
        generation_config_extra={"maxOutputTokens": max_tokens},
    )


def ai_tutor(question, source, target, context="", level=""):
    level_line = f"Learner proficiency (CEFR): {level}\n" if level else ""
    return ask(f"""You are TongueTie, a friendly multilingual language tutor.
Learner language: {source}
Target language: {target}
{level_line}Question: {question}
Relevant context:
{context}
Give a clear learner-friendly answer pitched at the learner's level. Include examples and a short practice task when useful.
Do not claim to have heard audio unless a transcript is provided.""")


def translate_text(text, source, target):
    return ask(f"""Translate from {source} to {target}.
Return a natural translation first, then a concise learning note if useful.
Preserve meaning, tone, names, and important formatting.
Text:
{text}""")


def translate_fast(text, source, target):
    """Minimal-latency translation for the "Fast answer" path.

    No learning note, no extra commentary, and a low output-token cap —
    output length is the biggest lever on response time for flash models,
    so keeping this to just the translation itself is what makes it fast.
    """
    prompt = (
        f"Translate the following text from {source} to {target}. "
        "Output ONLY the translation itself - no notes, no explanation, "
        "no quotation marks, nothing else.\n\n"
        f"Text:\n{text.strip()}"
    )
    return generate(
        [{"text": prompt}],
        temperature=0.2,
        generation_config_extra={"maxOutputTokens": 300},
    )


def correct_text(text, language):
    return ask(f"""Correct this {language} text for a language learner. Be concise.
Return:
1. Corrected version
2. What was wrong
3. Why
4. A more natural alternative when appropriate
Text:
{text}""", max_tokens=500)


def explain_word(word, source, target):
    """Kept deliberately short — a concise word card renders faster than a
    long one, and a quick lookup is what this feature is for."""
    prompt = f"""Teach the word/phrase "{word}" to someone who speaks {source} and is learning {target}.
Be concise. Include only: meaning (1 line), part of speech, pronunciation guidance (1 line), one example sentence, and one common mistake to avoid.
No extra sections, no preamble."""
    return ask(prompt, max_tokens=350)


def generate_quiz(source, target, topic, level=""):
    level_line = f"Learner proficiency (CEFR): {level}\n" if level else ""
    return ask(f"""Create a 10-question {target} language-learning quiz for a {source}-speaking learner.
{level_line}Topic: {topic}
Match question difficulty to the learner's level. Use clear multiple-choice questions and include an answer key at the end.""")


def lesson_plan(source, target, level, topic):
    return ask(f"""Create a practical 10-minute {target} lesson for a {source}-speaking learner.
Level: {level}
Topic: {topic}
Include dialogue, vocabulary, grammar, pronunciation focus, comprehension check, speaking task, and review.""")
