# TongueTie V3 AI client fix

The deployed screenshot showed `Cannot send a request, as the client has been closed.`

V3 removes the persistent google-genai text client entirely. Text AI calls now use Gemini's HTTPS REST `generateContent` endpoint with a short-lived HTTP request, so a closed SDK client cannot be reused across Streamlit reruns.

The voice transcription module remains separate and uses the Gemini transcription API.

After replacing the GitHub root files, reboot the Streamlit app and verify `GEMINI_API_KEY` and `GEMINI_MODEL` in Secrets.
