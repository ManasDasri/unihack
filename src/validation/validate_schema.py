import json
import os


def load_schema(schema_path):
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_field_wrapper(field_name, field_data):
    """
    Validate the structure returned by the extraction pipeline
    for a single field.
    """

    errors = []

    if not isinstance(field_data, dict):
        return [f"{field_name}: expected an object"]

    required_keys = {"value", "confidence", "source_snippet"}
    missing_keys = required_keys - field_data.keys()

    for key in missing_keys:
        errors.append(f"{field_name}: missing '{key}'")

    if "confidence" in field_data:
        valid_confidence = {"high", "medium", "low"}

        if field_data["confidence"] not in valid_confidence:
            errors.append(
                f"{field_name}: invalid confidence "
                f"'{field_data['confidence']}'"
            )

    return errors


def validate_product(extracted_data, schema):
    """
    Validate an extracted product against its category schema.

    Returns a validation report instead of modifying the extracted data.
    """

    errors = []

    if not isinstance(extracted_data, dict):
        return {
            "valid": False,
            "errors": ["Product data must be a JSON object"]
        }

    # Check top-level schema sections
    required_sections = {"common", "attributes"}

    for section in required_sections:
        if section not in extracted_data:
            errors.append(f"Missing section: {section}")

    # Validate fields defined by the schema
    for section in required_sections:
        if section not in extracted_data:
            continue

        section_data = extracted_data[section]

        if not isinstance(section_data, dict):
            errors.append(f"{section}: expected an object")
            continue

        schema_fields = schema.get(section, {})

        # Missing fields
        for field_name in schema_fields:
            if field_name not in section_data:
                errors.append(
                    f"{section}.{field_name}: missing field"
                )
                continue

            errors.extend(
                validate_field_wrapper(
                    f"{section}.{field_name}",
                    section_data[field_name]
                )
            )

        # Unexpected fields
        for field_name in section_data:
            if field_name not in schema_fields:
                errors.append(
                    f"{section}.{field_name}: unexpected field"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")

    schema_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "schema",
        "bearing.json"
    )

    extracted_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "extracted",
        "skf_6205.json"
    )

    schema = load_schema(schema_path)

    with open(extracted_path, "r") as f:
        extracted_data = json.load(f)

    result = validate_product(extracted_data, schema)

    print(json.dumps(result, indent=2))