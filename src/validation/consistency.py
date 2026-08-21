def _get_value(
    product: dict,
    field: str,
):
    """
    Safely retrieve an extracted field value.
    """

    for section in ("common", "attributes"):
        section_data = product.get(
            section,
            {},
        )

        field_data = section_data.get(
            field
        )

        if isinstance(field_data, dict):
            return field_data.get("value")

    return None


def _numeric(value):
    """
    Convert a value to float when possible.
    """

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def validate_bearing_consistency(
    product: dict,
) -> list[dict]:
    """
    Validate deterministic relationships between
    bearing attributes.
    """

    issues = []

    bore = _numeric(
        _get_value(
            product,
            "bore_diameter_mm",
        )
    )

    outer = _numeric(
        _get_value(
            product,
            "outer_diameter_mm",
        )
    )

    width = _numeric(
        _get_value(
            product,
            "width_mm",
        )
    )

    dynamic_load = _numeric(
        _get_value(
            product,
            "dynamic_load_rating_kn",
        )
    )

    static_load = _numeric(
        _get_value(
            product,
            "static_load_rating_kn",
        )
    )

    reference_speed = _numeric(
        _get_value(
            product,
            "reference_speed_rpm",
        )
    )

    limiting_speed = _numeric(
        _get_value(
            product,
            "limiting_speed_rpm",
        )
    )

    if (
        bore is not None
        and outer is not None
        and bore >= outer
    ):
        issues.append({
            "type": "dimension_conflict",
            "severity": "error",
            "fields": [
                "bore_diameter_mm",
                "outer_diameter_mm",
            ],
            "message": (
                "Bore diameter must be smaller "
                "than outer diameter."
            ),
        })

    if (
        width is not None
        and outer is not None
        and width >= outer
    ):
        issues.append({
            "type": "dimension_conflict",
            "severity": "error",
            "fields": [
                "width_mm",
                "outer_diameter_mm",
            ],
            "message": (
                "Bearing width must be smaller "
                "than outer diameter."
            ),
        })

    if (
        dynamic_load is not None
        and dynamic_load <= 0
    ):
        issues.append({
            "type": "invalid_value",
            "severity": "error",
            "fields": [
                "dynamic_load_rating_kn",
            ],
            "message": (
                "Dynamic load rating must be "
                "greater than zero."
            ),
        })

    if (
        static_load is not None
        and static_load <= 0
    ):
        issues.append({
            "type": "invalid_value",
            "severity": "error",
            "fields": [
                "static_load_rating_kn",
            ],
            "message": (
                "Static load rating must be "
                "greater than zero."
            ),
        })

    if (
        reference_speed is not None
        and reference_speed <= 0
    ):
        issues.append({
            "type": "invalid_value",
            "severity": "error",
            "fields": [
                "reference_speed_rpm",
            ],
            "message": (
                "Reference speed must be "
                "greater than zero."
            ),
        })

    if (
        limiting_speed is not None
        and limiting_speed <= 0
    ):
        issues.append({
            "type": "invalid_value",
            "severity": "error",
            "fields": [
                "limiting_speed_rpm",
            ],
            "message": (
                "Limiting speed must be "
                "greater than zero."
            ),
        })

    if (
        reference_speed is not None
        and limiting_speed is not None
        and reference_speed > limiting_speed
    ):
        issues.append({
            "type": "speed_conflict",
            "severity": "error",
            "fields": [
                "reference_speed_rpm",
                "limiting_speed_rpm",
            ],
            "message": (
                "Reference speed cannot exceed "
                "limiting speed."
            ),
        })

    return issues


def validate_consistency(
    product: dict,
) -> dict:
    """
    Run all deterministic consistency checks
    applicable to the product.
    """

    category = str(
        product.get(
            "category",
            "",
        )
    ).lower()

    issues = []

    if category == "bearing":
        issues.extend(
            validate_bearing_consistency(
                product
            )
        )

    errors = sum(
        1
        for issue in issues
        if issue["severity"] == "error"
    )

    warnings = sum(
        1
        for issue in issues
        if issue["severity"] == "warning"
    )

    return {
        "valid": errors == 0,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }