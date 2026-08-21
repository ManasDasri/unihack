import os

from src.enrichment.verify_evidence import (
    verify_field_evidence,
)


def verify_product_evidence(
    product: dict,
    pdf_path: str,
) -> dict:

    # Verify source evidence for every extracted product field.

    results = []

    for section in ("common", "attributes"):
        section_data = product.get(
            section,
            {},
        )

        if not isinstance(section_data, dict):
            continue

        for field, field_data in section_data.items():

            if not isinstance(field_data, dict):
                continue

            result = verify_field_evidence(
                field=field,
                field_data=field_data,
                pdf_path=pdf_path,
            )

            results.append(result)

    verified = sum(
        1
        for result in results
        if result["verified"] is True
    )

    unverified = sum(
        1
        for result in results
        if (
            result["verified"] is False
            and result["evidence"]["snippet"]
            and result["evidence"]["page"] is not None
        )
    )

    missing_evidence = sum(
        1
        for result in results
        if (
            not result["evidence"]["snippet"]
            or result["evidence"]["page"] is None
        )
    )

    conflicts = unverified

    total = len(results)

    return {
        "source": os.path.basename(pdf_path),
        "total_fields": total,
        "verified": verified,
        "unverified": unverified,
        "missing_evidence": missing_evidence,
        "conflicts": conflicts,
        "verification_rate": (
            verified / total
            if total
            else 0
        ),
        "fields": results,
    }