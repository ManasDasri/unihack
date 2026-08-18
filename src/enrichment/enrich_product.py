import copy
import json
import os


def get_value(product, section, field):
    """Safely retrieve the value of an extracted field."""

    section_data = product.get(section, {})

    if not isinstance(section_data, dict):
        return None

    field_data = section_data.get(field)

    if not isinstance(field_data, dict):
        return None

    return field_data.get("value")


def make_derived_field(value, source_fields, explanation):
    """Create a field using only deterministic source fields."""

    return {
        "value": value,
        "confidence": "high",
        "source_snippet": None,
        "provenance": {
            "type": "derived",
            "source_fields": source_fields,
            "explanation": explanation,
        },
    }


def derive_dimension_summary(product):
    """
    Derive a commerce-friendly dimension summary.

    Requires:
        bore diameter
        outside diameter
        width
    """

    bore = get_value(
        product,
        "attributes",
        "bore_diameter_mm",
    )

    outer_diameter = get_value(
        product,
        "attributes",
        "outer_diameter_mm",
    )

    width = get_value(
        product,
        "attributes",
        "width_mm",
    )

    if bore is None or outer_diameter is None or width is None:
        return None

    value = f"{bore} × {outer_diameter} × {width} mm"

    return make_derived_field(
        value=value,
        source_fields=[
            "attributes.bore_diameter_mm",
            "attributes.outer_diameter_mm",
            "attributes.width_mm",
        ],
        explanation=(
            "Dimension summary derived from bore diameter, "
            "outside diameter, and width extracted from "
            "the product source."
        ),
    )


def enrich_product(product):
    """
    Enrich a product using deterministic derivations.

    Missing source information is left missing.
    No manufacturer specifications are fabricated.
    """

    enriched = copy.deepcopy(product)

    attributes = enriched.setdefault(
        "attributes",
        {},
    )

    dimension_summary = derive_dimension_summary(
        enriched
    )

    if dimension_summary is not None:
        attributes["dimension_summary"] = dimension_summary

    return enriched


def build_enrichment_report(
    original_product,
    enriched_product,
):
    """Describe exactly what the enrichment stage added."""

    original_attributes = original_product.get(
        "attributes",
        {},
    )

    enriched_attributes = enriched_product.get(
        "attributes",
        {},
    )

    added_fields = []

    for field_name in enriched_attributes:
        if field_name not in original_attributes:
            added_fields.append(field_name)

    return {
        "enriched": len(added_fields) > 0,
        "added_fields": added_fields,
        "count": len(added_fields),
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

    extracted_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "extracted",
        "skf_6205.json",
    )

    with open(extracted_path, "r") as f:
        product = json.load(f)

    enriched_product = enrich_product(product)

    report = build_enrichment_report(
        product,
        enriched_product,
    )

    print(json.dumps(report, indent=2))

    print("\nDerived fields:")

    print(
        json.dumps(
            enriched_product.get(
                "attributes",
                {},
            ),
            indent=2,
        )
    )