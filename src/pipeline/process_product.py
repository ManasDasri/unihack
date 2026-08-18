import json
import os

from src.enrichment.enrich_product import (
    enrich_product,
    build_enrichment_report,
)
from src.validation.quality_report import build_quality_report
from src.validation.validate_schema import load_schema


class ProductPipeline:
    """Run an extracted product through validation and enrichment."""

    def __init__(self, schema_path):
        self.schema_path = schema_path
        self.schema = load_schema(schema_path)

    def process(self, product):
        """Validate, enrich, re-validate, and return one intelligence result."""

        initial_quality = build_quality_report(
            product,
            self.schema,
        )

        enriched_product = enrich_product(product)

        enrichment_report = build_enrichment_report(
            product,
            enriched_product,
        )

        final_quality = build_quality_report(
            enriched_product,
            self.schema,
        )

        decision = (
            "verified"
            if final_quality["status"] == "verified"
            else "review"
        )

        return {
            "product": enriched_product,
            "initial_quality": initial_quality,
            "enrichment": enrichment_report,
            "final_quality": final_quality,
            "decision": decision,
        }


def save_result(result, output_path):
    """Save the complete product-intelligence result as JSON."""

    output_directory = os.path.dirname(output_path)

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")

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

    output_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "extracted",
        "skf_6205_intelligence.json",
    )

    with open(extracted_path, "r") as f:
        product = json.load(f)

    pipeline = ProductPipeline(schema_path)
    result = pipeline.process(product)
    save_result(result, output_path)

    print(json.dumps(result, indent=2, ensure_ascii=False))
