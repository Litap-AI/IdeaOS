import re
from collections import Counter

STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "were", "which", "their",
    "have", "has", "for", "are", "was", "been", "into", "also", "than",
    "they", "these", "those", "will", "would", "about", "there", "while",
    "through", "between", "such", "more", "most", "other", "some", "using",
    "research", "paper", "study", "can", "may", "not", "but", "its", "our",
    "his", "her", "you", "who", "how", "what", "when", "where"
}


def _concepts(text: str, limit: int = 12):
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", text.lower())
    counts = Counter(w for w in words if w not in STOPWORDS)
    return [{"concept": w, "frequency": n} for w, n in counts.most_common(limit)]


def analyze_document(text: str, filename: str):
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Placeholder heuristic scores for MVP. These will become model-backed
    # metrics in the next implementation phase.
    novelty = min(95, max(10, 45 + min(35, len(set(words)) / max(1, word_count) * 100)))
    evidence = min(95, 40 + min(50, text.count("(") * 2 + text.count("[") * 3))
    argument_depth = min(95, 35 + min(55, len(paragraphs) * 1.5))

    return {
        "document": {
            "filename": filename,
            "word_count": word_count,
            "paragraph_count": len(paragraphs),
        },
        "idea_genome": {
            "novelty": round(novelty),
            "evidence": round(evidence),
            "influence": 50,
            "persuasion": 50,
            "concept_density": round(min(95, 20 + len(_concepts(text)) * 5)),
            "argument_depth": round(argument_depth),
        },
        "concepts": _concepts(text),
        "preview": text[:4000],
        "status": "mvp-analysis",
    }
