import json
import os


def get_value(data, section, field):
    """Safely retrieve an extracted field's value."""

    section_data = data.get(section, {})

    if not isinstance(section_data, dict):
        return None

    field_data = section_data.get(field)

    if not isinstance(field_data, dict):
        return None

    return field_data.get("value")


def check_rule(condition, rule, message, fields):
    """Create a consistency issue when a rule fails."""

    if condition:
        return None

    return {
        "rule": rule,
        "status": "failed",
        "message": message,
        "fields": fields,
    }


def validate_consistency(extracted_data):
    """
    Validate relationships between extracted product attributes.

    This function does not modify the extracted data.
    It returns a deterministic consistency report.
    """

    issues = []

    attributes = extracted_data.get("attributes", {})

    if not isinstance(attributes, dict):
        return {
            "valid": False,
            "issues": [{
                "rule": "attributes_section",
                "status": "failed",
                "message": "Attributes section must be an object.",
                "fields": ["attributes"],
            }]
        }

    # ---------------------------------------------------------
    # Dimensional consistency
    # ---------------------------------------------------------

    bore = get_value(
        extracted_data,
        "attributes",
        "bore_diameter_mm"
    )

    outer_diameter = get_value(
        extracted_data,
        "attributes",
        "outer_diameter_mm"
    )

    width = get_value(
        extracted_data,
        "attributes",
        "width_mm"
    )

    # Only evaluate a relationship when all required values exist.
    if bore is not None and outer_diameter is not None:

        issue = check_rule(
            bore < outer_diameter,
            "bore_less_than_outer_diameter",
            "Bore diameter must be smaller than outside diameter.",
            [
                "attributes.bore_diameter_mm",
                "attributes.outer_diameter_mm",
            ],
        )

        if issue:
            issues.append(issue)

    # Width must be positive when supplied.
    if width is not None:

        issue = check_rule(
            width > 0,
            "positive_width",
            "Bearing width must be greater than zero.",
            ["attributes.width_mm"],
        )

        if issue:
            issues.append(issue)

    # ---------------------------------------------------------
    # Speed consistency
    # ---------------------------------------------------------

    reference_speed = get_value(
        extracted_data,
        "attributes",
        "reference_speed_rpm"
    )

    limiting_speed = get_value(
        extracted_data,
        "attributes",
        "limiting_speed_rpm"
    )

    if reference_speed is not None and limiting_speed is not None:

        issue = check_rule(
            reference_speed >= limiting_speed,
            "reference_speed_not_less_than_limiting_speed",
            "Reference speed should not be lower than limiting speed.",
            [
                "attributes.reference_speed_rpm",
                "attributes.limiting_speed_rpm",
            ],
        )

        if issue:
            issues.append(issue)

    # ---------------------------------------------------------
    # Load-rating consistency
    # ---------------------------------------------------------

    dynamic_load = get_value(
        extracted_data,
        "attributes",
        "dynamic_load_rating_kn"
    )

    static_load = get_value(
        extracted_data,
        "attributes",
        "static_load_rating_kn"
    )

    if dynamic_load is not None and static_load is not None:

        issue = check_rule(
            dynamic_load > 0 and static_load > 0,
            "positive_load_ratings",
            "Load ratings must be greater than zero.",
            [
                "attributes.dynamic_load_rating_kn",
                "attributes.static_load_rating_kn",
            ],
        )

        if issue:
            issues.append(issue)

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    return {
        "valid": len(issues) == 0,
        "issues": issues,
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

    result = validate_consistency(extracted_data)

    print(json.dumps(result, indent=2))