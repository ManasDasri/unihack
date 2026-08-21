import pymupdf as pymu
import os


def extract_pdf(pdf_path):
    text = []

    with pymu.open(pdf_path) as doc:
        for page in doc:
            text.append(page.get_text("text", sort=True))

    return "\n".join(text)


def extract_pdf_pages(pdf_path):
    pages = []

    with pymu.open(pdf_path) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text", sort=True)

            pages.append({
                "page": page_number,
                "text": text,
            })

    return pages


def pages_to_text(pages):
    sections = []

    for page in pages:
        sections.append(
            f"--- PAGE {page['page']} ---\n"
            f"{page['text']}"
        )

    return "\n\n".join(sections)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")

    raw_dir = os.path.join(
        PROJECT_ROOT,
        "data",
        "raw",
    )

    for filename in os.listdir(raw_dir):
        if not filename.endswith(".pdf"):
            continue

        pdf_path = os.path.join(
            raw_dir,
            filename,
        )

        print(f"\nProcessing: {filename}")
        pages = extract_pdf_pages(pdf_path)
        print(f"Extracted {len(pages)} pages")
        
        for page in pages:
            print(f"\n--- PAGE {page['page']} ---")
            print(page["text"][:500])