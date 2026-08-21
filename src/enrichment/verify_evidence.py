import os

from src.ingestion.extract_text import (
    extract_pdf_pages,
)
from src.enrichment.evidence import (
    evidence_from_extracted_field,
    verify_snippet,
)


def verify_field_evidence(
    field: str,
    field_data: dict,
    pdf_path: str,
) -> dict:
    """
    Verify an extracted field's source snippet against
    the original PDF page.
    """

    evidence = evidence_from_extracted_field(
        field=field,
        field_data=field_data,
        source=os.path.basename(pdf_path),
    )

    page = field_data.get(
        "source_page"
    )

    snippet = field_data.get(
        "source_snippet"
    )

    if page is None or snippet is None:
        return evidence

    pages = extract_pdf_pages(
        pdf_path
    )

    matching_page = next(
        (
            item
            for item in pages
            if item["page"] == page
        ),
        None,
    )

    if matching_page is None:
        return evidence

    verified = verify_snippet(
        matching_page["text"],
        snippet,
    )

    evidence["verified"] = verified

    return evidence