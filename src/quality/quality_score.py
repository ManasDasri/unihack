def calculate_quality_score(
    extraction: dict,
    verification: dict,
    enrichment_results: list[dict] | None = None,
    validation_result: dict | None = None,
) -> dict:

    enrichment_results = (
        enrichment_results or []
    )

    total_fields = 0
    populated_fields = 0

    for section in (
        "common",
        "attributes",
    ):
        fields = extraction.get(
            section,
            {},
        )

        if not isinstance(fields, dict):
            continue

        for field_data in fields.values():
            if not isinstance(
                field_data,
                dict,
            ):
                continue

            total_fields += 1

            value = field_data.get(
                "value"
            )

            if value is not None and value != "":
                populated_fields += 1

    verified_fields = verification.get(
        "verified",
        0,
    )

    if total_fields:
        verified_fields = min(
            verified_fields,
            populated_fields,
        )

        evidence_score = (
            verified_fields / total_fields
        ) * 100
    else:
        evidence_score = 0

    confidence_values = []

    for section in (
        "common",
        "attributes",
    ):
        fields = extraction.get(
            section,
            {},
        )

        if not isinstance(fields, dict):
            continue

        for field_data in fields.values():
            if not isinstance(
                field_data,
                dict,
            ):
                continue

            value = field_data.get(
                "value"
            )

            if value is None or value == "":
                continue

            confidence = field_data.get(
                "confidence"
            )

            if confidence:
                confidence_values.append(
                    confidence
                )

    confidence_weights = {
        "high": 1.0,
        "medium": 0.6,
        "low": 0.3,
    }

    if total_fields:
        confidence_score = (
            sum(
                confidence_weights.get(
                    confidence,
                    0,
                )
                for confidence in confidence_values
            )
            / total_fields
        ) * 100
    else:
        confidence_score = 0

    if enrichment_results:
        verified_enrichments = sum(
            1
            for result in enrichment_results
            if result.get("verified") is True
        )

        enrichment_score = (
            verified_enrichments
            / len(enrichment_results)
        ) * 100
    else:
        enrichment_score = 100

    overall_score = (
        evidence_score * 0.50
        + confidence_score * 0.30
        + enrichment_score * 0.20
    )

    if overall_score >= 90:
        status = "commerce_ready"
    elif overall_score >= 75:
        status = "review_recommended"
    else:
        status = "needs_review"

    if (
        validation_result is not None
        and validation_result.get("status")
        != "verified"
    ):
        status = "review_recommended"

    return {
        "overall_score": round(
            overall_score,
            2,
        ),
        "evidence_score": round(
            evidence_score,
            2,
        ),
        "confidence_score": round(
            confidence_score,
            2,
        ),
        "enrichment_score": round(
            enrichment_score,
            2,
        ),
        "status": status,
    }