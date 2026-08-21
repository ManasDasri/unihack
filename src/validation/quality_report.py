import json
import os

from .validate_schema import (
    load_schema,
    validate_product,
)
from .validate_values import (
    validate_values,
)
from .validate_consistency import (
    validate_consistency,
)


def get_field_data(product, section, field):
    """Safely retrieve a field object from an extracted product."""

    section_data = product.get(section, {})

    if not isinstance(section_data, dict):
        return None

    field_data = section_data.get(field)

    if not isinstance(field_data, dict):
        return None

    return field_data


def calculate_field_metrics(product, schema):
    """
    Calculate field coverage and evidence coverage.

    Coverage:
        How many schema-defined fields contain a value?

    Evidence coverage:
        How many populated fields have supporting source evidence?
    """

    total_fields = 0
    populated_fields = 0
    evidence_fields = 0

    confidence_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for section_name in ("common", "attributes"):
        schema_section = schema.get(
            section_name,
            {},
        )

        if not isinstance(
            schema_section,
            dict,
        ):
            continue

        for field_name in schema_section:
            total_fields += 1

            field_data = get_field_data(
                product,
                section_name,
                field_name,
            )

            if field_data is None:
                continue

            value = field_data.get("value")

            if value is not None:
                populated_fields += 1

                source_snippet = field_data.get(
                    "source_snippet"
                )

                if (
                    isinstance(
                        source_snippet,
                        str,
                    )
                    and source_snippet.strip()
                ):
                    evidence_fields += 1

                confidence = field_data.get(
                    "confidence"
                )

                if confidence in confidence_counts:
                    confidence_counts[
                        confidence
                    ] += 1

    coverage = (
        populated_fields / total_fields
        if total_fields
        else 0
    )

    evidence_coverage = (
        evidence_fields / populated_fields
        if populated_fields
        else 0
    )

    return {
        "total_fields": total_fields,
        "populated_fields": populated_fields,
        "field_coverage": round(
            coverage,
            3,
        ),
        "fields_with_evidence": evidence_fields,
        "evidence_coverage": round(
            evidence_coverage,
            3,
        ),
        "confidence": confidence_counts,
    }


def determine_status(
    schema_result,
    value_result,
    consistency_result,
    field_metrics,
):
    """
    Determine the product's overall validation status.

    VERIFIED:
        All validation layers pass and every schema-defined
        field contains a value.

    REVIEW:
        The product has structural, value, consistency,
        or completeness problems.

    REJECTED:
        Reserved for future hard-failure rules.
        We currently do not use this automatically.
    """

    if not schema_result["valid"]:
        return "review"

    if not value_result["valid"]:
        return "review"

    if not consistency_result["valid"]:
        return "review"

    if (
        field_metrics["populated_fields"]
        < field_metrics["total_fields"]
    ):
        return "review"

    return "verified"


def build_quality_report(product, schema):
    """
    Run all validation layers and produce one product-quality report.
    """

    schema_result = validate_product(
        product,
        schema,
    )

    value_result = validate_values(
        product,
    )

    consistency_result = validate_consistency(
        product,
    )

    metrics = calculate_field_metrics(
        product,
        schema,
    )

    status = determine_status(
        schema_result,
        value_result,
        consistency_result,
        metrics,
    )

    total_issues = (
        len(
            schema_result.get(
                "errors",
                [],
            )
        )
        + len(
            value_result.get(
                "errors",
                [],
            )
        )
        + len(
            consistency_result.get(
                "issues",
                [],
            )
        )
    )

    return {
        "status": status,
        "summary": {
            "schema_valid": schema_result[
                "valid"
            ],
            "values_valid": value_result[
                "valid"
            ],
            "consistency_valid": consistency_result[
                "valid"
            ],
            "total_issues": total_issues,
        },
        "coverage": {
            "total_fields": metrics[
                "total_fields"
            ],
            "populated_fields": metrics[
                "populated_fields"
            ],
            "field_coverage": metrics[
                "field_coverage"
            ],
            "fields_with_evidence": metrics[
                "fields_with_evidence"
            ],
            "evidence_coverage": metrics[
                "evidence_coverage"
            ],
        },
        "confidence": metrics[
            "confidence"
        ],
        "validation": {
            "schema": schema_result,
            "values": value_result,
            "consistency": consistency_result,
        },
    }


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    PROJECT_ROOT = os.path.join(
        SCRIPT_DIR,
        "..",
        "..",
    )

    schema_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "schema",
        "bearing.json",
    )

    extracted_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "extracted",
        "skf_6205.json",
    )

    schema = load_schema(
        schema_path
    )

    with open(
        extracted_path,
        "r",
    ) as f:
        product = json.load(f)

    report = build_quality_report(
        product,
        schema,
    )

    print(
        json.dumps(
            report,
            indent=2,
        )
    )