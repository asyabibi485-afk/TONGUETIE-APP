# TongueTie AI Service Client

This build removes the reusable `google-genai` client from the text AI layer and
uses stateless HTTPS REST requests instead. Speech transcription also uses the
Gemini Files + Interactions REST APIs.

## Why this fixes the recurring error

The deployed app repeatedly showed:

`Cannot send a request, as the client has been closed.`

The REST implementation does not create, cache, or reuse a Google SDK client,
so a Streamlit rerun cannot accidentally send a request through a closed client.
Each request has its own HTTP connection, timeout and bounded retry behavior.

## Current API flow

- Text AI: `POST /v1beta/interactions`
- Speech upload: `POST /upload/v1beta/files` (resumable upload)
- Speech transcription: `POST /v1beta/interactions` with `gemini-3.5-transcribe`
- Browser playback: Web Speech API, best-effort female/male voice selection

The current Gemini documentation describes Interactions as the recommended
standard interface, and the transcription guide documents REST audio upload +
`gemini-3.5-transcribe` transcription.

## Secrets

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODELS = "gemini-3.8-flash"
GEMINI_TRANSCRIBE_MODEL = "gemini-3.5-transcribe"
TONGUETIE_ADMIN_PASSWORD = "YOUR_ADMIN_PASSWORD"
```

Never commit the real API key to GitHub.
