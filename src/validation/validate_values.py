import json
import os
import math


NUMERIC_FIELDS = {
    "bore_diameter_mm",
    "outer_diameter_mm",
    "width_mm",
    "dynamic_load_rating_kn",
    "static_load_rating_kn",
    "reference_speed_rpm",
    "limiting_speed_rpm",
    "carbon_footprint_kg_co2e",
    "net_weight_kg",
}


STRING_FIELDS = {
    "name",
    "manufacturer",
    "part_number",
    "description",
    "material",
    "cage_type",
    "sealing",
    "radial_internal_clearance",
    "performance_class",
    "eclass_code",
    "unspsc_code",
}


def is_valid_number(value):
    """
    Check whether a value is a real numeric value.

    Booleans are explicitly rejected because Python considers
    bool to be a subclass of int.
    """

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    if isinstance(value, float) and not math.isfinite(value):
        return False

    return True


def validate_field_value(field_name, field_data):
    """
    Validate the actual value contained inside an extracted field.
    """

    errors = []

    if not isinstance(field_data, dict):
        return [f"{field_name}: expected field object"]

    value = field_data.get("value")

    # Missing values are allowed at this stage.
    # Enrichment/review logic can decide what to do with them later.
    if value is None:
        return errors

    if field_name in NUMERIC_FIELDS:
        if not is_valid_number(value):
            errors.append(
                f"{field_name}: expected numeric value, got "
                f"{type(value).__name__}"
            )

    elif field_name in STRING_FIELDS:
        if not isinstance(value, str):
            errors.append(
                f"{field_name}: expected string value, got "
                f"{type(value).__name__}"
            )

    return errors


def validate_values(extracted_data):
    """
    Validate the values inside an extracted product.

    Returns a report without modifying the original product data.
    """

    errors = []

    if not isinstance(extracted_data, dict):
        return {
            "valid": False,
            "errors": ["Product data must be a JSON object"]
        }

    for section_name in ("common", "attributes"):
        section = extracted_data.get(section_name)

        if not isinstance(section, dict):
            continue

        for field_name, field_data in section.items():
            errors.extend(
                validate_field_value(
                    field_name,
                    field_data
                )
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")

    extracted_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "extracted",
        "skf_6205.json"
    )

    with open(extracted_path, "r") as f:
        extracted_data = json.load(f)

    result = validate_values(extracted_data)

    print(json.dumps(result, indent=2))