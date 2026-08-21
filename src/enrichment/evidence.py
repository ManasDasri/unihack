from typing import Any


EVIDENCE_METHODS = {
    "source",
    "derived",
    "retrieved",
    "inferred",
    "unknown",
}


def build_evidence(
    field: str,
    value: Any,
    method: str,
    confidence: str,
    snippet: str | None = None,
    source: str | None = None,
    page: int | None = None,
    verified: bool = False,
) -> dict:
    """
    Build a normalized evidence record for a product field.
    """

    if method not in EVIDENCE_METHODS:
        raise ValueError(
            f"Invalid evidence method: {method}"
        )

    if confidence not in {
        "high",
        "medium",
        "low",
    }:
        raise ValueError(
            f"Invalid confidence: {confidence}"
        )

    return {
        "field": field,
        "value": value,
        "method": method,
        "confidence": confidence,
        "verified": verified,
        "evidence": {
            "snippet": snippet,
            "source": source,
            "page": page,
        },
    }


def evidence_from_extracted_field(
    field: str,
    field_data: dict,
    source: str | None = None,
) -> dict:
    """
    Convert an extracted field into the normalized
    evidence format.

    The evidence is initially unverified because the
    extracted snippet has not yet been checked against
    the original document.
    """

    return build_evidence(
        field=field,
        value=field_data.get("value"),
        method="source",
        confidence=field_data.get(
            "confidence",
            "low",
        ),
        snippet=field_data.get(
            "source_snippet"
        ),
        source=source,
        page=field_data.get(
            "source_page"
        ),
    )


def evidence_is_supported(evidence: dict) -> bool:
    """
    Determine whether an evidence record contains
    supporting evidence.
    """

    evidence_data = evidence.get(
        "evidence",
        {},
    )

    snippet = evidence_data.get(
        "snippet"
    )

    return (
        isinstance(snippet, str)
        and bool(snippet.strip())
    )


def verify_snippet(
    page_text: str,
    snippet: str | None,
) -> bool:
    """
    Verify that an extracted evidence snippet exists
    in the claimed PDF page.

    Matching is whitespace-normalized because PDF text
    extraction can produce inconsistent spacing.
    """

    if not isinstance(page_text, str):
        return False

    if not isinstance(snippet, str):
        return False

    normalized_page = " ".join(
        page_text.split()
    ).lower()

    normalized_snippet = " ".join(
        snippet.split()
    ).lower()

    if not normalized_snippet:
        return False

    return normalized_snippet in normalized_page