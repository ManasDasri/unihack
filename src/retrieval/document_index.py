import os

from src.ingestion.extract_text import extract_pdf_pages


class DocumentIndex:

    # Lightweight in-memory index over page-aware PDF text.
    # Each indexed page keeps its source document and page number
    # so retrieved evidence can retain provenance.

    def __init__(self):
        self.pages = []

    def add_pdf(self, pdf_path):
        pages = extract_pdf_pages(pdf_path)

        filename = os.path.basename(pdf_path)

        for page in pages:
            self.pages.append({
                "source": filename,
                "page": page["page"],
                "text": page["text"],
            })

    def add_directory(self, directory):
        for filename in sorted(
            os.listdir(directory)
        ):
            if not filename.lower().endswith(".pdf"):
                continue

            self.add_pdf(
                os.path.join(
                    directory,
                    filename,
                )
            )

    def search(self, query, limit=5):
        """
        Search indexed pages using phrase and term matching
        across both document text and source filename.
        """

        normalized_query = " ".join(
            query.lower().split()
        )

        terms = {
            term
            for term in normalized_query.split()
            if term
        }

        results = []

        for page in self.pages:
            text = " ".join(
                page["text"].lower().split()
            )

            source = " ".join(
                page["source"].lower().split()
            )

            searchable_text = (
                f"{source} {text}"
            )

            phrase_match = (
                normalized_query
                in searchable_text
            )

            term_matches = sum(
                1
                for term in terms
                if term in searchable_text
            )

            if (
                not phrase_match
                and term_matches == 0
            ):
                continue

            score = (
                10
                if phrase_match
                else 0
            ) + term_matches

            results.append({
                **page,
                "score": score,
            })

        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results[:limit]