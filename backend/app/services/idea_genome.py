import re
from collections import Counter
from typing import Any

STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "among",
    "also",
    "although",
    "because",
    "before",
    "being",
    "between",
    "could",
    "during",
    "each",
    "from",
    "further",
    "have",
    "having",
    "into",
    "more",
    "most",
    "other",
    "over",
    "same",
    "should",
    "such",
    "than",
    "their",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "under",
    "using",
    "very",
    "were",
    "which",
    "while",
    "with",
    "would",
    "your",
}


NOISE_TERMS = {
    "table",
    "figure",
    "fig",
    "crossref",
    "score",
    "scores",
    "section",
    "sections",
    "page",
    "pages",
    "article",
    "study",
    "paper",
    "author",
    "authors",
    "result",
    "results",
}


ACADEMIC_SIGNAL_TERMS = {
    "analysis",
    "model",
    "method",
    "methodology",
    "framework",
    "approach",
    "algorithm",
    "classification",
    "verification",
    "detection",
    "prediction",
    "learning",
    "neural",
    "network",
    "feature",
    "features",
    "evidence",
    "validity",
    "reliability",
    "accuracy",
    "performance",
    "explainability",
    "reproducibility",
    "robustness",
    "generalization",
}


def normalize_text(text: str) -> str:
    """Normalize text while preserving meaningful words."""
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    """Extract normalized alphabetic tokens."""
    return re.findall(
        r"\b[a-zA-Z][a-zA-Z'-]{2,}\b",
        text.lower(),
    )


def is_valid_term(term: str) -> bool:
    """Reject obvious extraction noise."""
    term = term.lower().strip()

    if term in STOPWORDS:
        return False

    if term in NOISE_TERMS:
        return False
    return len(term) >= 4

    return True


def extract_candidate_phrases(
    text: str,
    max_words: int = 3,
) -> list[str]:
    """
    Extract unigram, bigram and trigram candidates.
    """
    tokens = [
        token
        for token in tokenize(text)
        if is_valid_term(token)
    ]

    candidates = []

    for size in range(1, max_words + 1):
        for index in range(
            len(tokens) - size + 1
        ):
            phrase_tokens = tokens[
                index:index + size
            ]

            phrase = " ".join(
                phrase_tokens
            )

            candidates.append(phrase)

    return candidates


def calculate_phrase_scores(
    text: str,
) -> dict[str, float]:
    """
    Score candidate concepts using frequency,
    academic terminology and phrase length.

    This is intentionally transparent and deterministic.
    """
    candidates = extract_candidate_phrases(text)

    frequencies = Counter(candidates)

    scores: dict[str, float] = {}

    for phrase, frequency in frequencies.items():

        words = phrase.split()

        score = float(frequency)
        if len(words) == 1 and frequency < 5:
            continue
        if len(words) > 1 and frequency < 2:
            continue

        # Multi-word concepts are generally
        # more informative than isolated words.
        if len(words) == 2:
            score *= 2.5
        elif len(words) >= 3:
            score *= 4.0

        # Reward recognized academic terminology.
        signal_hits = sum(
            word in ACADEMIC_SIGNAL_TERMS
            for word in words
        )

        score += signal_hits * 2.5

        scores[phrase] = round(
            score,
            3,
        )

    return scores


def select_concepts(
    text: str,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """
    Produce the Idea Genome concept candidates.
    """
    scores = calculate_phrase_scores(text)

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    concepts = []

    for rank, (
        phrase,
        score,
    ) in enumerate(
        ranked[:limit],
        start=1,
    ):
        frequency = len(
            re.findall(
                rf"\b{re.escape(phrase)}\b",
                text,
                re.IGNORECASE,
            )
        )

        concepts.append(
            {
                "id": f"concept_{rank}",
                "name": phrase,
                "frequency": frequency,
                "score": score,
                "rank": rank,
            }
        )

    return concepts


def is_useful_context(sentence: str) -> bool:
    lower = sentence.lower()
    metadata_signals = [
        "article ",
        "correspondence:",
        "department of",
        "faculty of",
        "university",
        "hospital",
        "email",
        "©",
        "doi",
        "http",
        "received:",
        "accepted:",
        "published:",
    ]
    if any(
        signal in lower
        for signal in metadata_signals
    ):
        return False
    return len(sentence.split()) >= 8
    

def find_concept_contexts(
    text: str,
    concepts: list[dict[str, Any]],
    max_contexts: int = 3,
) -> list[dict[str, Any]]:
    """
    Find short contextual snippets where concepts appear.
    """
    sentences = re.split(
        r"(?<=[.!?])\s+",
        normalize_text(text),
    )

    for concept in concepts:
        matches = []

        pattern = re.compile(
            rf"\b{re.escape(concept['name'])}\b",
            re.IGNORECASE,
        )

        for sentence in sentences:

            if not is_useful_context(sentence):
                continue

            if pattern.search(sentence):
                matches.append(
                    sentence[:500]
                )

            if len(matches) >= max_contexts:
                break

        concept["contexts"] = matches

    return concepts


def build_concept_relationships(
    concepts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build simple co-occurrence relationships
    between concepts.

    Concepts are related when they repeatedly appear
    in the same contextual snippets.
    """
    relationships = []

    for index, source in enumerate(concepts):

        source_context = " ".join(
            source.get("contexts", [])
        ).lower()

        for target in concepts[index + 1:]:

            target_name = target["name"].lower()

            if target_name in source_context:
                relationships.append(
                    {
                        "source": source["id"],
                        "target": target["id"],
                        "relationship": "co_occurs",
                    }
                )

    return relationships


def build_idea_genome(
    text: str,
    limit: int = 30,
) -> dict[str, Any]:
    """
    Main Idea Genome entry point.
    """
    concepts = select_concepts(
        text,
        limit=limit,
    )

    concepts = find_concept_contexts(
        text,
        concepts,
    )

    relationships = (
        build_concept_relationships(
            concepts
        )
    )

    return {
        "concepts": concepts,
        "relationships": relationships,
        "concept_count": len(concepts),
        "relationship_count": len(
            relationships
        ),
    }
