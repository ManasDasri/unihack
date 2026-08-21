import json

from src.retrieval.document_index import (
    DocumentIndex,
)
from src.retrieval.retrieve_evidence import (
    retrieve_evidence,
)


class CorpusEnricher:

    def __init__(
        self,
        client,
        index: DocumentIndex,
    ):
        self.client = client
        self.index = index

    @staticmethod
    def _field_value(
        product: dict,
        field: str,
    ):
        value = product.get(field)

        if isinstance(value, dict):
            return value.get("value")

        return value

    def _product_identifier(
        self,
        product: dict,
    ):
        product_identifier = self._field_value(
            product.get(
                "common",
                {},
            ),
            "part_number",
        )

        if not product_identifier:
            product_identifier = self._field_value(
                product,
                "product_id",
            )

        return str(
            product_identifier or ""
        ).strip().lower()

    def _category(
        self,
        product: dict,
    ):
        category = self._field_value(
            product,
            "category",
        )

        if not category:
            category = self._field_value(
                product.get(
                    "common",
                    {},
                ),
                "category",
            )

        return str(
            category or ""
        ).strip().lower()

    def build_prompt(
        self,
        product: dict,
        field: str,
        candidates: list[dict],
    ) -> str:
        evidence = json.dumps(
            candidates,
            indent=2,
            ensure_ascii=False,
        )

        product_identifier = (
            self._product_identifier(
                product
            )
        )

        category = self._category(
            product
        )

        return f"""
You are enriching an industrial product catalog.

Product:
- product identifier: {product_identifier or "unknown"}
- category: {category or "unknown"}
- missing field: {field}

Retrieved evidence from the product document corpus:
{evidence}

Rules:
- Use ONLY the retrieved evidence above.
- Do not use outside knowledge.
- Do not guess or infer unsupported values.
- If the evidence does not clearly support a value, return null.
- The source snippet must be copied exactly from the retrieved evidence.
- The source page must match the retrieved evidence.
- The source must match the retrieved evidence.
- Return only valid JSON.

Return exactly:
{{
  "value": ...,
  "confidence": "high" | "medium" | "low",
  "source_snippet": "...",
  "source": "...",
  "source_page": ...,
  "reason": "..."
}}
"""

    def enrich_field(
        self,
        product: dict,
        field: str,
    ) -> dict:

        product_identifier = (
            self._product_identifier(
                product
            )
        )

        category = self._category(
            product
        )

        retrieval_query = " ".join(
            part
            for part in (
                product_identifier,
                category,
                field,
            )
            if part
        )

        candidates = retrieve_evidence(
            self.index,
            retrieval_query,
            limit=10,
            field=field,

        )
        filtered_candidates = []

        for candidate in candidates:
            source = str(
                candidate.get(
                    "source",
                    "",
                )
            ).strip().lower()

            product_match = bool(
                product_identifier
                and product_identifier in source
            )

            if product_match:
                filtered_candidates.append(
                    candidate
                )

        candidates = filtered_candidates

        if not candidates:
            return {
                "value": None,
                "confidence": "low",
                "source_snippet": None,
                "source": None,
                "source_page": None,
                "reason": (
                    "No retrieved evidence was found "
                    "for the target product."
                ),
            }

        prompt = self.build_prompt(
            product,
            field,
            candidates,
        )

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0,
            response_format={
                "type": "json_object",
            },
        )

        return json.loads(
            response.choices[0].message.content
        )