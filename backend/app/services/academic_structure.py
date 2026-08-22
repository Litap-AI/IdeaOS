import re
from typing import Any

SECTION_ALIASES = {
    "abstract": {
        "abstract",
        "summary",
    },
    "introduction": {
        "introduction",
        "background",
    },
    "literature_review": {
        "literature review",
        "review of literature",
        "related work",
        "related studies",
        "state of the art",
    },
    "methodology": {
        "methodology",
        "method",
        "methods",
        "materials and methods",
        "research methodology",
        "experimental methods",
    },
    "results": {
        "results",
        "findings",
        "results and findings",
    },
    "discussion": {
        "discussion",
        "analysis and discussion",
        "results and discussion",
    },
    "conclusion": {
        "conclusion",
        "conclusions",
        "concluding remarks",
        "summary and conclusion",
    },
    "references": {
        "references",
        "bibliography",
        "works cited",
        "literature cited",
    },
}


SECTION_ORDER = [
    "abstract",
    "introduction",
    "literature_review",
    "methodology",
    "results",
    "discussion",
    "conclusion",
    "references",
]


def normalize_line(line: str) -> str:
    """
    Normalize whitespace and common PDF extraction artifacts.
    """
    line = line.replace("\u00ad", "")
    line = line.replace("­", "")
    line = re.sub(r"\s+", " ", line)

    return line.strip()


def normalize_heading(line: str) -> str:
    """
    Convert a possible heading into a normalized comparison string.
    """
    line = normalize_line(line)

    # Remove common section numbering:
    # 1. Introduction
    # 1 Introduction
    # 1.1 Methods
    # II. Introduction
    line = re.sub(
        r"^(?:"
        r"\d+(?:\.\d+)*"
        r"|[IVXLCDM]+"
        r"|[IVXLCDM]+\."
        r")"
        r"[\s.)-]+",
        "",
        line,
        flags=re.IGNORECASE,
    )

    return line.strip(" .:-").lower()


def classify_heading(line: str) -> str | None:
    """
    Determine whether a line is a recognized academic section heading.
    """
    normalized = normalize_heading(line)

    for section_name, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section_name

    return None


def looks_like_numbered_heading(line: str) -> bool:
    """
    Detect likely numbered academic headings.
    """
    normalized = normalize_line(line)

    return bool(
        re.match(
            r"^(?:"
            r"\d+(?:\.\d+)*"
            r"|[IVXLCDM]+"
            r")"
            r"[\s.)-]+"
            r"[A-Z][A-Za-z0-9 ,:&'()/\-]{2,100}$",
            normalized,
        )
    )


def looks_like_heading(line: str) -> bool:
    """
    General heading heuristic.

    We intentionally keep this conservative so normal sentences
    are not accidentally classified as headings.
    """
    line = normalize_line(line)

    if not line:
        return False

    if len(line) > 120:
        return False

    if line.endswith((".", "?", "!")):
        return False

    if classify_heading(line):
        return True

    if looks_like_numbered_heading(line):
        return True

    # Short all-uppercase headings.
    return (
        len(line.split()) <= 10
        and line.upper() == line
        and re.search(r"[A-Z]", line)
    )


def clean_text_lines(text: str) -> list[str]:
    """
    Convert extracted PDF text into usable lines.
    """
    lines = []

    for raw_line in text.splitlines():
        line = normalize_line(raw_line)

        if line:
            lines.append(line)

    return lines


def detect_title(lines: list[str]) -> str | None:
    """
    Attempt to identify the paper title from the first part of the document.
    """
    for index, line in enumerate(lines[:80]):

        if line.lower() in {
            "article",
            "research article",
            "original article",
        }:
            continue

        if classify_heading(line):
            break

        # Ignore journal metadata and publication boilerplate.
        if re.search(
            r"^(received|revised|accepted|published|copyright|"
            r"license|academic editor|doi|issn)\b",
            line,
            re.IGNORECASE,
        ):
            continue

        # Titles are usually reasonably long and don't look like metadata.
        if 5 <= len(line.split()) <= 30:
            return line

    return None


def detect_authors(lines: list[str], title: str | None) -> list[str]:
    """
    Detect likely author names near the title.
    """
    if not title:
        return []

    try:
        title_index = lines.index(title)
    except ValueError:
        title_index = 0

    candidates = lines[
        title_index + 1:title_index + 12
    ]

    authors = []

    for line in candidates:

        if re.search(
            r"\b(department|university|faculty|hospital|"
            r"correspondence|email|@)\b",
            line,
            re.IGNORECASE,
        ):
            continue

        if classify_heading(line):
            break

        # Conservative author heuristic:
        # 2-8 tokens, mostly alphabetic.
        words = line.replace(",", " ").split()

        if 2 <= len(words) <= 12:

            alpha_ratio = sum(
                char.isalpha()
                for char in line
            ) / max(len(line), 1)

            if alpha_ratio > 0.75:
                authors.append(line)

        if len(authors) >= 5:
            break

    return authors


def extract_doi(text: str) -> str | None:
    """
    Extract DOI if present.
    """
    match = re.search(
        r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b",
        text,
        re.IGNORECASE,
    )

    return match.group(0) if match else None


def extract_date(
    text: str,
    label: str,
) -> str | None:
    """
    Extract publication workflow dates such as:
    Received: ...
    Revised: ...
    Accepted: ...
    Published: ...
    """
    pattern = rf"\b{re.escape(label)}\s*:\s*([^\n]+)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    return (
        normalize_line(match.group(1))
        if match
        else None
    )


def extract_keywords(text: str) -> list[str]:
    """
    Extract keyword lists from common academic formats.
    """
    patterns = [
        r"(?:keywords|key words)\s*:\s*(.+)",
        r"(?:keywords|key words)\s*[-–]\s*(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        raw_keywords = match.group(1)

        raw_keywords = re.split(
            r"[;\n|•]",
            raw_keywords,
        )

        keywords = [
            normalize_line(keyword).strip(".,;:")
            for keyword in raw_keywords
            if normalize_line(keyword)
        ]

        return keywords[:30]

    return []


def split_into_sections(
    lines: list[str],
) -> list[dict[str, Any]]:
    """
    Split the document using detected academic headings.
    """
    sections: list[dict[str, Any]] = []

    current = {
        "name": "front_matter",
        "heading": None,
        "lines": [],
    }

    for line in lines:

        section_name = classify_heading(line)

        if section_name:

            if current["lines"] or current["name"] != "front_matter":
                sections.append(current)

            current = {
                "name": section_name,
                "heading": line,
                "lines": [],
            }

            continue

        current["lines"].append(line)

    if current["lines"] or current["name"] != "front_matter":
        sections.append(current)

    return sections


def build_section_output(
    sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert internal sections into API-friendly objects.
    """
    output = []

    for section in sections:

        text = " ".join(section["lines"]).strip()

        output.append(
            {
                "name": section["name"],
                "heading": section["heading"],
                "paragraph_count": count_paragraphs(
                    text
                ),
                "word_count": len(
                    re.findall(r"\b\w+\b", text)
                ),
                "preview": text[:700],
            }
        )

    return output


def count_paragraphs(text: str) -> int:
    """
    Approximate paragraph count from extracted text.
    """
    if not text.strip():
        return 0

    paragraphs = re.split(
        r"\n\s*\n+",
        text,
    )

    return len(
        [
            paragraph
            for paragraph in paragraphs
            if paragraph.strip()
        ]
    )


def calculate_structure_confidence(
    sections: list[dict[str, Any]],
) -> float:
    """
    Estimate how confidently the system identified
    the document structure.

    This is a diagnostic score, NOT an AI quality score.
    """
    detected = {
        section["name"]
        for section in sections
        if section["name"] != "front_matter"
    }

    expected = {
        "abstract",
        "introduction",
        "methodology",
        "references",
    }

    if not detected:
        return 0.0

    matched = len(
        detected.intersection(expected)
    )

    return round(
        min(
            matched / len(expected),
            1.0,
        ),
        2,
    )


def analyze_academic_structure(
    text: str,
) -> dict[str, Any]:
    """
    Main AcademicStructureEngine entry point.
    """
    lines = clean_text_lines(text)

    title = detect_title(lines)

    authors = detect_authors(
        lines,
        title,
    )

    sections = split_into_sections(lines)

    section_output = build_section_output(
        sections
    )

    structure_confidence = (
        calculate_structure_confidence(
            sections
        )
    )

    return {
        "metadata": {
            "title": title,
            "authors": authors,
            "doi": extract_doi(text),
            "received": extract_date(
                text,
                "Received",
            ),
            "revised": extract_date(
                text,
                "Revised",
            ),
            "accepted": extract_date(
                text,
                "Accepted",
            ),
            "published": extract_date(
                text,
                "Published",
            ),
            "keywords": extract_keywords(text),
        },
        "structure": {
            "sections": section_output,
            "section_count": len(section_output),
            "detected_section_types": [
                section["name"]
                for section in section_output
            ],
            "confidence": structure_confidence,
        },
    }
