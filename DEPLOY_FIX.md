# TongueTie — Streamlit ImportError Fix

The screenshot showed an `ImportError` at:

`from gemini_service import (...)`

This build removes the top-level dependency. `gemini_service` is loaded only when
an AI feature is used. `google-genai` is also imported only when a Gemini request
is made.

## IMPORTANT
Upload the **contents** of this ZIP to the root of your GitHub repository.

The repository root must contain:

- `app.py`
- `gemini_service.py`
- `rag.py`
- `language_data.py`
- `speech_service.py`
- `requirements.txt`
- `data/knowledge_base.txt`

In Streamlit Cloud:
- Main file path: `app.py`
- Reboot the app after pushing.

Secrets:
```toml
GEMINI_API_KEY = "your-real-key"
GEMINI_MODEL = "your-enabled-gemini-model"
TONGUETIE_ADMIN_PASSWORD = "your-admin-password"
```

Do not put the real API key in GitHub.
