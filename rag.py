
from pathlib import Path
import re

KB = Path(__file__).parent / "data" / "knowledge_base.txt"


def retrieve_context(query, top_k=4):
    """Best-effort keyword retrieval over the local knowledge base.

    Returns "" (never raises) if the knowledge-base file is missing, so a
    missing/renamed data file degrades the AI Tutor's context instead of
    crashing the whole page.
    """
    try:
        text = KB.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return ""
    chunks = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    terms = set(re.findall(r"\w+", query.lower()))
    scored = []
    for chunk in chunks:
        words = set(re.findall(r"\w+", chunk.lower()))
        score = len(terms & words)
        scored.append((score, chunk))
    scored.sort(reverse=True, key=lambda x:x[0])
    return "\n\n".join(c for s,c in scored[:top_k] if s > 0) or "\n\n".join(chunks[:top_k])
