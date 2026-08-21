import json
import os

from dotenv import load_dotenv
from groq import Groq

from src.enrichment.enrich_product import (
    enrich_product,
    build_enrichment_report,
)
from src.enrichment.verify_product import (
    verify_product_evidence,
)
from src.quality.quality_score import (
    calculate_quality_score,
)
from src.retrieval.document_index import (
    DocumentIndex,
)
from src.retrieval.enrich_from_corpus import (
    CorpusEnricher,
)
from src.retrieval.verify_enrichment import (
    verify_enrichment,
)
from src.validation.quality_report import (
    build_quality_report,
)
from src.validation.validate_consistency import (
    validate_consistency,
)
from src.validation.validate_schema import (
    load_schema,
)
from src.ingestion.extract_text import (
    extract_pdf_pages,
)

load_dotenv()


class ProductPipeline:
    """
    Run an extracted product through the complete
    product-intelligence pipeline.

    Pipeline:

        validation
        -> source evidence verification
        -> deterministic enrichment
        -> corpus enrichment
        -> enrichment verification
        -> consistency validation
        -> quality scoring
        -> final decision
    """

    def __init__(
        self,
        schema_dir,
        pdf_path=None,
        document_index=None,
        groq_client=None,
    ):
        self.schema_dir = schema_dir
        self.pdf_path = pdf_path
        self.document_index = document_index
        self.groq_client = groq_client

    def _get_category(self, product):
        category = product.get("category")

        if isinstance(category, dict):
            return category.get("value")

        if isinstance(category, str):
            return category

        return None

    def _load_product_schema(self, product):
        category = self._get_category(product)

        if not category:
            return None

        schema_path = os.path.join(
            self.schema_dir,
            f"{category.lower()}.json",
        )

        if not os.path.exists(schema_path):
            return None

        return load_schema(schema_path)

    def _get_missing_fields(
        self,
        product,
        schema,
    ):
        """
        Return schema fields that are not populated
        in the extracted product.
        """

        missing = []

        if not isinstance(schema, dict):
            return missing

        attributes_schema = schema.get(
            "attributes",
            {},
        )

        attributes = product.get(
            "attributes",
            {},
        )

        if not isinstance(
            attributes_schema,
            dict,
        ):
            return missing

        if not isinstance(
            attributes,
            dict,
        ):
            attributes = {}

        for field in attributes_schema:
            field_data = attributes.get(field)

            if not isinstance(
                field_data,
                dict,
            ):
                missing.append(field)
                continue

            value = field_data.get("value")

            if value is None or value == "":
                missing.append(field)

        return missing

    def _enrich_missing_fields(
        self,
        product,
        schema,
        pdf_path,
    ):
        """
        Attempt evidence-backed enrichment only for
        fields that are actually missing.
        """

        if (
            self.document_index is None
            or self.groq_client is None
        ):
            return product, []

        missing_fields = self._get_missing_fields(
            product,
            schema,
        )

        if not missing_fields:
            return product, []

        enricher = CorpusEnricher(
            self.groq_client,
            self.document_index,
        )

        pages = []

        if pdf_path:
            pages = extract_pdf_pages(
                pdf_path
            )

        enrichment_results = []

        for field in missing_fields:
            result = enricher.enrich_field(
                product,
                field,
            )

            if result.get("value") is None:
                enrichment_results.append({
                    **result,
                    "field": field,
                    "verified": False,
                    "status": "unknown",
                })
                continue

            # Ensure the evidence actually points to the correct target product document
            if pdf_path and result.get("source") != os.path.basename(pdf_path):
                enrichment_results.append({
                    **result,
                    "field": field,
                    "verified": False,
                    "status": "invalid_source",
                })
                continue

            verified = verify_enrichment(
                result,
                pages,
            )

            verified["field"] = field

            enrichment_results.append(
                verified
            )

            if verified.get(
                "verified"
            ) is not True:
                continue

            if "attributes" not in product:
                product["attributes"] = {}

            product["attributes"][field] = {
                "value": verified["value"],
                "method": "retrieved",
                "confidence": verified.get(
                    "confidence",
                    "low",
                ),
                "source_snippet": verified.get("source_snippet"),
                "source_page": verified.get("source_page"),
            }

        return product, enrichment_results

    def process(self, product):
        """
        Process one extracted product and return
        a complete intelligence result.
        """

        schema = self._load_product_schema(
            product
        )

        if schema is None:
            return {
                "product": product,
                "initial_quality": {
                    "status": "review",
                    "reason": (
                        "No schema is available "
                        "for the product category."
                    ),
                },
                "evidence": None,
                "enrichment": None,
                "corpus_enrichment": [],
                "consistency": None,
                "final_quality": {
                    "status": "review",
                    "reason": (
                        "No schema is available "
                        "for the product category."
                    ),
                },
                "quality_score": {
                    "overall_score": 0,
                    "status": "needs_review",
                },
                "decision": "review",
            }

        initial_quality = build_quality_report(
            product,
            schema,
        )

        evidence_report = None

        if self.pdf_path:
            evidence_report = (
                verify_product_evidence(
                    product,
                    self.pdf_path,
                )
            )

        enriched_product = enrich_product(
            product
        )

        enrichment_report = (
            build_enrichment_report(
                product,
                enriched_product,
            )
        )

        enriched_product, corpus_results = (
            self._enrich_missing_fields(
                enriched_product,
                schema,
                self.pdf_path,
            )
        )

        consistency_report = (
            validate_consistency(
                enriched_product
            )
        )

        final_quality = build_quality_report(
            enriched_product,
            schema,
        )

        quality_score = calculate_quality_score(
            enriched_product,
            evidence_report or {},
            corpus_results,
            final_quality,

        )

        quality_valid = (
            final_quality["status"]
            == "verified"
        )

        consistency_valid = (
            consistency_report["valid"]
        )

        evidence_valid = True

        if evidence_report is not None:
            evidence_valid = (
                evidence_report.get(
                    "unverified",
                    0,
                ) == 0
                and evidence_report.get(
                    "missing_evidence",
                    0,
                ) == 0
            )

        enrichment_valid = all(
            result.get("verified") is True
            for result in corpus_results
        )

        score_valid = (
            quality_score["status"]
            == "commerce_ready"
        )

        if (
            quality_valid
            and consistency_valid
            and evidence_valid
            and enrichment_valid
            and score_valid
        ):
            decision = "verified"
        else:
            decision = "review"

        return {
            "product": enriched_product,
            "initial_quality": initial_quality,
            "evidence": evidence_report,
            "enrichment": enrichment_report,
            "corpus_enrichment": corpus_results,
            "consistency": consistency_report,
            "final_quality": final_quality,
            "quality_score": quality_score,
            "decision": decision,
        }


def save_result(
    result,
    output_path,
):
    """
    Save the complete product-intelligence result
    as JSON.
    """

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:
        os.makedirs(
            output_directory,
            exist_ok=True,
        )

    with open(
        output_path,
        "w",
    ) as f:
        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False,
        )


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

    pdf_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "raw",
        "skf_6205.pdf",
    )

    schema_dir = os.path.join(
        PROJECT_ROOT,
        "data",
        "schema",
    )

    output_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "extracted",
        "skf_6205_intelligence.json",
    )

    with open(
        extracted_path,
        "r",
    ) as f:
        product = json.load(f)

    client = Groq()

    index = DocumentIndex()

    index.add_directory(
        os.path.join(
            PROJECT_ROOT,
            "data",
            "raw",
        )
    )

    pipeline = ProductPipeline(
        schema_dir=schema_dir,
        pdf_path=pdf_path,
        document_index=index,
        groq_client=client,
    )

    result = pipeline.process(
        product
    )

    save_result(
        result,
        output_path,
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )