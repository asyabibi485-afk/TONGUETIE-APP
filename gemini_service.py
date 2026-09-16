"""TongueTie AI service client.

REST-only Gemini client designed for Streamlit Cloud.

Why REST-only?
- Streamlit reruns application code frequently.
- A long-lived SDK client can become invalid/closed between reruns.
- This module creates no persistent Gemini client and keeps no network session.
- Every request is a short-lived HTTPS request with explicit timeout/retry handling.

The Interactions API is used for text generation. See the official Gemini API
reference for the current recommended interface.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable


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
            "and reboot the app."
        )
    return key.strip()


def _model() -> str:
    return (_setting("GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash").strip()


def _models_to_try() -> list[str]:
    primary = _model()
    fallback_raw = _setting("GEMINI_FALLBACK_MODELS", "gemini-3.8-flash") or ""
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
    # Current Interactions response commonly exposes output_text.
    direct = obj.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    # Be tolerant of response-shape variations.
    outputs = obj.get("outputs") or []
    pieces: list[str] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        text = output.get("text")
        if isinstance(text, str) and text.strip():
            pieces.append(text)
        for content in output.get("content") or []:
            if isinstance(content, dict):
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    pieces.append(text)

    if pieces:
        return "\n".join(pieces).strip()

    # Legacy generateContent compatibility, useful if a model/provider returns
    # the older response shape.
    for candidate in obj.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                pieces.append(part["text"])
    return "\n".join(pieces).strip()


def ask(prompt: str, *, temperature: float = 0.3) -> str:
    """Send one stateless text request to Gemini.

    No SDK client is created, cached, closed, or reused. This directly avoids
    the Streamlit error: "Cannot send a request, as the client has been closed."
    """
    if not prompt or not prompt.strip():
        return "AI service error: empty prompt."

    payload = {
        "model": _model(),
        "input": [{"type": "text", "text": prompt.strip()}],
        "generation_config": {"temperature": max(0.0, min(float(temperature), 1.0))},
    }
    last: Exception | None = None
    for model in _models_to_try():
        payload["model"] = model
        try:
            result = _json_request(f"{API_BASE}/interactions", payload)
            text = _extract_text(result)
            if text:
                return text
            last = RuntimeError("Gemini returned no text output.")
        except RuntimeError as exc:
            last = exc
            # Try the configured fallback model only for model availability errors.
            message = str(exc).lower()
            if not any(token in message for token in ("not found", "unsupported", "model")):
                break

    return f"AI service error: {last or 'Unknown Gemini error.'}"


def ai_tutor(question, source, target, context=""):
    return ask(f"""You are TongueTie, a friendly multilingual language tutor.
Learner language: {source}
Target language: {target}
Question: {question}
Relevant context:
{context}
Give a clear learner-friendly answer. Include examples and a short practice task when useful.
Do not claim to have heard audio unless a transcript is provided.""")


def translate_text(text, source, target):
    return ask(f"""Translate from {source} to {target}.
Return a natural translation first, then a concise learning note if useful.
Preserve meaning, tone, names, and important formatting.
Text:
{text}""")


def correct_text(text, language):
    return ask(f"""Correct this {language} text for a language learner.
Return:
1. Corrected version
2. What was wrong
3. Why
4. A more natural alternative when appropriate
Text:
{text}""")


def explain_word(word, source, target):
    return ask(f"""Teach the word/phrase "{word}" to someone who speaks {source} and is learning {target}.
Include meaning, part of speech, pronunciation guidance, 2 examples, common mistakes, related words, and one short practice question.""")


def generate_quiz(source, target, topic):
    return ask(f"""Create a 10-question {target} language-learning quiz for a {source}-speaking learner.
Topic: {topic}
Use clear multiple-choice questions and include an answer key at the end.""")


def lesson_plan(source, target, level, topic):
    return ask(f"""Create a practical 10-minute {target} lesson for a {source}-speaking learner.
Level: {level}
Topic: {topic}
Include dialogue, vocabulary, grammar, pronunciation focus, comprehension check, speaking task, and review.""")
