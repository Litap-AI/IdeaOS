import re
from collections import Counter

from app.services.academic_structure import (
    analyze_academic_structure,
)
from app.services.idea_genome import (
    build_idea_genome,
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

def normalize_citations(citations):
    """
    Convert raw citation strings into structured references.

    Only bracketed numeric citations such as [5], [5,6],
    or [3,4,10] are treated as numbered references.
    Other numeric text, such as publication years in
    '(NIPS 1993)', is preserved but produces no references.
    """

    normalized = []

    for citation in citations:

        citation = citation.strip()

        if re.fullmatch(
            r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]",
            citation,
        ):
            references = [
                int(number)
                for number in re.findall(
                    r"\d+",
                    citation,
                )
            ]
        else:
            references = []

        normalized.append(
            {
                "raw": citation,
                "references": references,
            }
        )

    return normalized


def is_claim_candidate(sentence: str) -> bool:
    """
    Reject obvious non-claim artifacts such as tables,
    metadata blocks, and reference fragments.
    """

    text = sentence.lower().strip()

    metadata_signals = [
        "funding:",
        "correspondence:",
        "author contributions:",
        "conflict of interest",
        "data availability",
    ]

    if any(signal in text for signal in metadata_signals):
        return False

    if "doi.org/" in text:
        return False

    words = sentence.split()

    numeric_tokens = sum(
        any(char.isdigit() for char in word)
        for word in words
    )

    if len(words) >= 30 and numeric_tokens / len(words) > 0.25:
        return False

    table_signals = [
        "metric ai",
        "ai (train)",
        "ai (test)",
        "expert 1",
        "expert 2",
        "expert 3",
        "p-value",
    ]

    return sum(
        signal in text
        for signal in table_signals
    ) < 2

def classify_claim(sentence: str) -> tuple[str, float]:
    """
    Classify a candidate sentence into a broad academic claim type.

    Returns:
        (claim_type, confidence)
    """

    text = sentence.lower().strip()

    metadata_signals = [
        "funding:",
        "correspondence:",
        "author contributions:",
        "conflict of interest",
        "data availability",
        "supplementary materials",
        "acknowledgments",
        "received no external funding",
    ]

    if any(signal in text for signal in metadata_signals):
        return "metadata", 0.98

    future_signals = [
        "future work",
        "future research",
        "will therefore",
        "will prioritise",
        "will prioritize",
        "remains an open question",
    ]

    if any(signal in text for signal in future_signals):
        return "future_work", 0.94

    limitation_signals = [
    "should not be generalised",
    "should not be generalized",
    "cannot be generalised",
    "cannot be generalized",
    "remains an open question",
    "limited to",
    "limitation",
    "under unrestricted",
    "low-skill",
    "skilled or adversarial",
]
    if any(
        signal in text
        for signal in limitation_signals
):
        return "limitation", 0.92

    method_signals = [
        "we propose",
        "we developed",
        "we designed",
        "we collected",
        "samples were collected",
        "participants",
        "dataset",
        "method",
        "architecture",
    ]

    if any(signal in text for signal in method_signals):
        return "methodological", 0.82

    background_signals = [
    "previously",
    "prior studies",
    "prior research",
    "previous studies",
    "published literature",
    "literature has",
    "have achieved",
    "has achieved",
    "have demonstrated",
    "has demonstrated",
]
    if any(
        signal in text
        for signal in background_signals
    ):
        return "background", 0.88

    finding_signals = [
        "achieved",
        "improved",
        "outperformed",
        "significantly",
        "accuracy",
        "f1-score",
        "auc-roc",
        "results show",
        "results indicate",
        "results suggest",
        "our findings",
    ]

    if any(signal in text for signal in finding_signals):
        return "finding", 0.90

    interpretation_signals = [
        "therefore",
        "thus",
        "suggests",
        "indicates",
        "demonstrates",
        "argues",
        "because",
        "confirm",
        "confirms",
    ]

    if any(signal in text for signal in interpretation_signals):
        return "interpretation", 0.84

    return "general", 0.60


def extract_claims(paragraphs):
    """
    Extract likely research claims from academic paragraphs.

    Uses deterministic linguistic and research-result signals.
    This is a baseline claim detector, not an LLM classifier.
    """

    claim_pattern = re.compile(
        r"\b("
        r"therefore|"
        r"thus|"
        r"argues?|"
        r"claims?|"
        r"suggests?|"
        r"demonstrates?|"
        r"shows?|"
        r"indicates?|"
        r"reveals?|"
        r"finds?|"
        r"found that|"
        r"we propose|"
        r"we argue|"
        r"we found|"
        r"this study|"
        r"this research|"
        r"the findings|"
        r"the results|"
        r"results show|"
        r"results indicate|"
        r"results suggest|"
        r"achieved|"
        r"improved|"
        r"outperformed|"
        r"significant|"
        r"significantly|"
        r"correlated|"
        r"associated"
        r")\b",
        re.IGNORECASE,
    )

    claims = []

    for paragraph_index, paragraph in enumerate(paragraphs):

        sentences = re.split(
            r"(?<=[.!?])\s+",
            paragraph.strip(),
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if len(sentence.split()) < 10:
                continue

            if not is_claim_candidate(sentence):
                continue
            if not claim_pattern.search(sentence):
                continue

            claim_type, confidence = classify_claim(sentence)
            claims.append(
                {
                    "id": f"claim_{len(claims) + 1}",
                    "paragraph": paragraph_index + 1,
                    "text": sentence,
                    "type": claim_type,
                    "confidence": confidence,
                    "citations": extract_citations(sentence),
                }
            )

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

def link_claims_to_concepts(
    claims,
    concepts,
    max_links: int = 5,
):
    """
    Link claims to relevant Idea Genome concepts.

    Uses:
    1. Exact multi-word concept matching
    2. Common academic/AI acronym matching
    3. Idea Genome concept scores for ranking

    Limits each claim to a maximum of 5 concepts
    to prevent noisy relationships.
    """
    acronym_expansions = {
        "cnn": "convolutional neural networks",
        "cnns": "convolutional neural networks",
        "rnn": "recurrent neural networks",
        "rnns": "recurrent neural networks",
        "ai": "artificial intelligence",
        "ml": "machine learning",
        "nlp": "natural language processing",
    }
    for claim in claims:

        claim_text = claim["text"].lower()

        matches = []

        # -------------------------------------------------
        # 1. Exact multi-word concept matching
        # -------------------------------------------------

        for concept in concepts:

            concept_name = (
                concept["name"]
                .lower()
                .strip()
            )

            if not concept_name:
                continue

            # Ignore generic single-word concepts.
            if len(concept_name.split()) == 1:
                continue

            if concept_name in claim_text:

                matches.append(
                    {
                        "id": concept["id"],
                        "score": concept.get(
                            "score",
                            0,
                        ),
                    }
                )

        # -------------------------------------------------
        # 2. Acronym / technical concept matching
        # -------------------------------------------------

        for acronym, expansion in acronym_expansions.items():

            if not re.search(
                rf"\b{re.escape(acronym)}\b",
                claim_text,
            ):
                continue

            for concept in concepts:

                concept_name = (
                    concept["name"]
                    .lower()
                    .strip()
                )

                if concept_name == expansion:

                    matches.append(
                        {
                            "id": concept["id"],
                            "score": concept.get(
                                "score",
                                0,
                            ) + 10,
                        }
                    )

        # -------------------------------------------------
        # 3. Remove duplicate concept matches
        # -------------------------------------------------

        unique_matches = {}

        for match in matches:

            concept_id = match["id"]

            if (
                concept_id not in unique_matches
                or match["score"]
                > unique_matches[concept_id]["score"]
            ):
                unique_matches[concept_id] = match

        # -------------------------------------------------
        # 4. Rank concepts by Idea Genome score
        # -------------------------------------------------

        ranked_matches = sorted(
            unique_matches.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        # -------------------------------------------------
        # 5. Keep only the strongest relationships
        # -------------------------------------------------

        claim["concepts"] = [
            match["id"]
            for match in ranked_matches[:max_links]
        ]

    return claims

def build_claim_citation_relationships(
    claims,
):
    """
    Build relationships between claims and
    the numbered references cited by those claims.
    """

    relationships = []

    for claim in claims:

        for citation in claim.get(
            "citations",
            [],
        ):

            numbers = re.findall(
                r"\d+",
                citation,
            )

            for number in numbers:

                reference_id = int(number)

                relationships.append(
                    {
                        "source": claim["id"],
                        "target": f"reference_{reference_id}",
                        "type": "supported_by",
                    }
                )

    return relationships


def build_graph(concepts, claims, citations):
    nodes = []
    edges = []

    node_ids = set()
    edge_keys = set()

    # --------------------------------
    # Helper: add node safely
    # --------------------------------

    def add_node(node):
        node_id = node["id"]

        if node_id in node_ids:
            return

        node_ids.add(node_id)
        nodes.append(node)

    # --------------------------------
    # Concept nodes
    # --------------------------------

    for concept in concepts:

        add_node({
            "id": concept["id"],
            "label": concept["name"],
            "type": "concept",
            "size": min(
                42,
                14 + concept.get("frequency", 0) * 2
            )
        })

    # --------------------------------
    # Claim nodes
    # --------------------------------

    for claim in claims:

        claim_id = claim["id"]
        claim_text = claim.get("text", "")

        add_node({
            "id": claim_id,
            "label": claim_text[:70],
            "type": "claim",
            "size": 10
        })

        # --------------------------------
        # Claim -> Concept relationships
        # --------------------------------

        claim_text_lower = claim_text.lower()

        for concept in concepts:

            concept_name = concept.get("name", "").lower()

            if not concept_name:
                continue

            if concept_name not in claim_text_lower:
                continue

            edge_key = (
                claim_id,
                concept["id"],
                "mentions",
            )

            if edge_key in edge_keys:
                continue

            edge_keys.add(edge_key)

            edges.append({
                "source": claim_id,
                "target": concept["id"],
                "type": "mentions"
            })

    # --------------------------------
    # Reference nodes
    # --------------------------------

    for citation in citations:

        # Ignore malformed citation objects
        if not isinstance(citation, dict):
            continue

        references = citation.get("references", [])

        if not isinstance(references, list):
            continue

        for reference_number in references:

            reference_id = (
                f"reference_{reference_number}"
            )

            add_node({
                "id": reference_id,
                "label": f"Reference {reference_number}",
                "type": "reference",
                "size": 8
            })

    # --------------------------------
    # Claim -> Reference relationships
    # --------------------------------

    for claim in claims:

        claim_id = claim["id"]

        claim_citations = claim.get(
            "citations",
            []
        )

        if not isinstance(claim_citations, list):
            continue

        for citation in claim_citations:

            if not isinstance(citation, str):
                continue

            numbers = re.findall(
                r"\d+",
                citation
            )

            for number in numbers:

                reference_id = (
                    f"reference_{number}"
                )

                # --------------------------------
                # Make sure reference node exists
                # --------------------------------

                if reference_id not in node_ids:

                    add_node({
                        "id": reference_id,
                        "label": f"Reference {number}",
                        "type": "reference",
                        "size": 8
                    })

                # --------------------------------
                # Create relationship
                # --------------------------------

                edge_key = (
                    claim_id,
                    reference_id,
                    "supported_by",
                )

                if edge_key in edge_keys:
                    continue

                edge_keys.add(edge_key)

                edges.append({
                    "source": claim_id,
                    "target": reference_id,
                    "type": "supported_by"
                })

    # --------------------------------
    # Return graph
    # --------------------------------

    return {
        "nodes": nodes,
        "edges": edges[:200]
    }



def analyze_document_structure(text: str):

    paragraphs = split_paragraphs(text)

    academic_structure = analyze_academic_structure(text)

    raw_citations = extract_citations(text)
    citations = normalize_citations(raw_citations)
    print("CITATIONS TYPE:", type(citations))
    print("FIRST CITATION:", citations[0] if citations else None)
    idea_genome = build_idea_genome(
        text,
        limit=30
    )   

    claims = extract_claims(paragraphs)
    concepts = idea_genome["concepts"]
    claims = link_claims_to_concepts(
    claims,
    concepts,
    )

    claim_citation_relationships = (
        build_claim_citation_relationships(
               claims,
    )
)

    graph = build_graph(
        concepts,
        claims,
        citations
    )
    graph["edges"].extend(
        claim_citation_relationships
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
        "idea_genome": idea_genome,
        "claims": claims,
        "claim_citation_relationships": (
        claim_citation_relationships
        ),
        "graph": graph,
    }
