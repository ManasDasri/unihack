from src.enrichment.evidence import verify_snippet


def verify_enrichment(
    enrichment: dict,
    pages: list[dict],
) -> dict:
    """
    Independently verify an enrichment result against
    the original page-aware document text.
    """

    value = enrichment.get("value")
    snippet = enrichment.get("source_snippet")
    source_page = enrichment.get("source_page")

    if value is None:
        return {
            **enrichment,
            "verified": False,
            "status": "unknown",
        }

    if not snippet or source_page is None:
        return {
            **enrichment,
            "verified": False,
            "status": "missing_evidence",
        }

    page = next(
        (
            item
            for item in pages
            if item["page"] == source_page
        ),
        None,
    )

    if page is None:
        return {
            **enrichment,
            "verified": False,
            "status": "invalid_page",
        }

    verified = verify_snippet(
        page["text"],
        snippet,
    )

    return {
        **enrichment,
        "verified": verified,
        "status": (
            "verified"
            if verified
            else "conflict"
        ),
    }