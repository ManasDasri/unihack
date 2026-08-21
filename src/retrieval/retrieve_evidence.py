from src.retrieval.document_index import (
    DocumentIndex,
)


def extract_context(
    text: str,
    query: str,
    window: int = 180,
) -> str:
    normalized_text = " ".join(
        text.split()
    )

    terms = [
        term.lower()
        for term in query.split()
        if term.strip()
    ]

    if not terms:
        return normalized_text[:window]

    normalized_lower = normalized_text.lower()

    positions = [
        normalized_lower.find(term)
        for term in terms
    ]

    positions = [
        position
        for position in positions
        if position >= 0
    ]

    if not positions:
        return normalized_text[:window]

    start = max(
        0,
        min(positions) - window // 2,
    )

    end = min(
        len(normalized_text),
        start + window,
    )

    return normalized_text[start:end]


def retrieve_evidence(
    index: DocumentIndex,
    query: str,
    limit: int = 5,
    field: str | None = None,
) -> list[dict]:
    results = index.search(
        query,
        limit=limit,
    )

    evidence = []

    for result in results:
        evidence.append({
            "source": result["source"],
            "page": result["page"],
            "score": result["score"],
            "snippet": extract_context(
                result["text"],
                field or query,
            ),
        })

    return evidence