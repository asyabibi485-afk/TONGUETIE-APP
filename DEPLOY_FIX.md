# TongueTie deployment

1. Put these files directly in the GitHub repository root:
   - `app.py`
   - `gemini_service.py`
   - `speech_service.py`
   - `language_data.py`
   - `rag.py`
   - `requirements.txt`
   - `data/knowledge_base.txt`
2. In Streamlit Cloud, choose `app.py` as the main file.
3. Add the values from `.streamlit/secrets.toml.example` to Streamlit Secrets.
4. Reboot the app after pushing the new files.

Do not upload the ZIP as a nested directory. The modules must be beside `app.py`.
