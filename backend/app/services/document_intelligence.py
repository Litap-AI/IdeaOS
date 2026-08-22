import re
from collections import Counter

from app.services.academic_structure import (
    analyze_academic_structure,
)

STOPWORDS = {
    "about", "after", "again", "against", "also", "among",
    "because", "before", "being", "between", "could",
    "first", "from", "have", "into", "more", "most",
    "other", "over", "same", "should", "such", "than",
    "that", "their", "there", "these", "they", "this",
    "through", "under", "using", "were", "which",
    "while", "with", "would", "research", "paper",
    "study", "studies", "author", "authors"
}


SECTION_PATTERNS = [
    ("abstract", r"^\s*abstract\s*$"),
    ("introduction", r"^\s*(1[\.\)]\s*)?introduction\s*$"),
    ("literature_review",
     r"^\s*(2[\.\)]\s*)?(literature review|review of literature)\s*$"),
    ("methodology",
     r"^\s*(3[\.\)]\s*)?(methodology|methods|research methodology)\s*$"),
    ("results", r"^\s*(4[\.\)]\s*)?results?\s*$"),
    ("discussion", r"^\s*(5[\.\)]\s*)?discussion\s*$"),
    ("conclusion", r"^\s*(6[\.\)]\s*)?conclusions?\s*$"),
    ("references", r"^\s*(references|bibliography|works cited)\s*$"),
]


def split_paragraphs(text: str):
    blocks = re.split(r"\n\s*\n+", text)

    return [
        re.sub(r"\s+", " ", block).strip()
        for block in blocks
        if block.strip()
    ]


def detect_sections(paragraphs):
    sections = []
    current = {
        "name": "front_matter",
        "paragraphs": []
    }

    for paragraph in paragraphs:

        detected = None

        for name, pattern in SECTION_PATTERNS:
            if re.match(pattern, paragraph, flags=re.IGNORECASE):
                detected = name
                break

        if detected:

            sections.append(current)

            current = {
                "name": detected,
                "paragraphs": []
            }

        else:
            current["paragraphs"].append(paragraph)

    sections.append(current)

    return [
        section
        for section in sections
        if section["paragraphs"] or section["name"] != "front_matter"
    ]


def extract_citations(text: str):

    patterns = [

        # Harvard-style
        r"\([A-Z][A-Za-z'’-]+(?:\s+et al\.)?,?\s*\d{4}[a-z]?\)",

        # Numbered citations
        r"\[[0-9]{1,3}(?:\s*,\s*[0-9]{1,3})*\]"
    ]

    citations = []

    for pattern in patterns:
        citations.extend(
            re.findall(pattern, text)
        )

    return list(dict.fromkeys(citations))


def extract_claims(paragraphs):

    claim_pattern = re.compile(
        r"\b("
        r"therefore|"
        r"thus|"
        r"argues?|"
        r"suggests?|"
        r"demonstrates?|"
        r"shows?|"
        r"indicates?|"
        r"reveals?|"
        r"we propose|"
        r"we argue|"
        r"this study|"
        r"results show"
        r")\b",
        re.IGNORECASE
    )

    claims = []

    for paragraph_index, paragraph in enumerate(paragraphs):

        sentences = re.split(
            r"(?<=[.!?])\s+",
            paragraph
        )

        for sentence in sentences:

            if len(sentence.split()) < 10:
                continue

            if claim_pattern.search(sentence):

                claims.append({
                    "id": f"claim_{len(claims) + 1}",
                    "paragraph": paragraph_index + 1,
                    "text": sentence,
                    "citations": extract_citations(sentence)
                })

    return claims[:50]


def extract_concepts(text: str, limit=20):

    words = re.findall(
        r"[A-Za-z][A-Za-z'-]{4,}",
        text.lower()
    )

    filtered_words = [
        word
        for word in words
        if word not in STOPWORDS
    ]

    frequencies = Counter(filtered_words)

    concepts = []

    for index, (word, frequency) in enumerate(
        frequencies.most_common(limit)
    ):

        concepts.append({
            "id": f"concept_{index + 1}",
            "label": word,
            "frequency": frequency
        })

    return concepts


def build_graph(concepts, claims):

    nodes = []
    edges = []

    # Concept nodes
    for concept in concepts:

        nodes.append({
            "id": concept["id"],
            "label": concept["label"],
            "type": "concept",
            "size": min(
                42,
                14 + concept["frequency"] * 2
            )
        })

    # Claim nodes
    for claim in claims:

        nodes.append({
            "id": claim["id"],
            "label": claim["text"][:70],
            "type": "claim",
            "size": 10
        })

        claim_text = claim["text"].lower()

        for concept in concepts:

            if concept["label"] in claim_text:

                edges.append({
                    "source": claim["id"],
                    "target": concept["id"],
                    "type": "mentions"
                })

    return {
        "nodes": nodes,
        "edges": edges[:100]
    }


def analyze_document_structure(text: str):

    paragraphs = split_paragraphs(text)

    academic_structure = analyze_academic_structure(text)

    citations = extract_citations(text)

    concepts = extract_concepts(text)

    claims = extract_claims(paragraphs)

    graph = build_graph(
        concepts,
        claims
    )

    return {

        "stats": {
            "words": len(
                re.findall(r"\b\w+\b", text)
            ),
            "paragraphs": len(paragraphs),
            "sections": academic_structure[
            "structure"
            ]["section_count"],
            "citations": len(citations),
            "claims": len(claims),
            "concepts": len(concepts)
        },
        "metadata": academic_structure[
        "metadata"
        ],
        "structure": academic_structure[
        "structure"
        ],
        "citations": citations[:100],
        "concepts": concepts,
        "claims": claims,
        "graph": graph,
    }
