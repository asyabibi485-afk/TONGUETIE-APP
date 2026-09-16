# Streamlit Cloud deployment

1. Push the **contents of this folder** to the root of your GitHub repository.
2. In Streamlit Cloud, set Main file path to `app.py`.
3. In App Settings → Secrets, add:
   `GEMINI_API_KEY = "your-key"`
   `GEMINI_MODEL = "a-model-enabled-for-your-account"`
   `TONGUETIE_ADMIN_PASSWORD = "change-this"`
4. Reboot the app.

Do not upload your real API key to GitHub.

## Why the previous ZIP failed

The previous package placed `app.py` and `gemini_service.py` inside `streamlit_app/`.
If `app.py` was copied to the repository root while `gemini_service.py` stayed in the
subfolder, Python could not import the requested functions. This package puts all
Streamlit backend modules beside the root `app.py`.
