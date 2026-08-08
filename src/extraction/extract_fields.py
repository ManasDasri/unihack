import os
import json
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "data", "schema", "bearing.json") #organising filesystem

def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def build_prompt(raw_text, schema):
    schema_str = json.dumps(schema, indent=2)
    return f"""You are extracting structured product data from a bearing datasheet.

Below is the target schema. For each field, return an object with:
- "value": the extracted value (or null if not found)
- "confidence": "high", "medium", or "low"
- "source_snippet": the exact short text from the document that supports this value (or null if not found)

Schema:
{schema_str}

Document text:
{raw_text}

Be precise about matching each value to its correct label. Do not confuse nearby but unrelated numbers (for example, net weight and carbon footprint are different values, even if they appear close together in the text).

Return ONLY valid JSON matching this structure — no explanation, no markdown formatting, just the JSON object. Every field in "common" and "attributes" should be present, each as {{"value": ..., "confidence": ..., "source_snippet": ...}}.
"""

def extract_fields(raw_text):
    schema = load_schema()
    prompt = build_prompt(raw_text, schema)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw_output = response.choices[0].message.content
    # strip markdown fences if the model adds them anyway
    cleaned = raw_output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)

if __name__ == "__main__":
    from src.ingestion.extract_text import extract_pdf
    from src.extraction.classify_category import classify_category

    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    output_dir = os.path.join(PROJECT_ROOT, "data", "extracted")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(raw_dir):
        if not filename.endswith(".pdf"):
            continue
        pdf_path = os.path.join(raw_dir, filename)
        print(f"Processing {filename}...")
        raw_text = extract_pdf(pdf_path)

        classification = classify_category(raw_text)
        print(f"  Classified as: {classification['category']} ({classification['confidence']}) - {classification['reasoning']}")

        if classification["category"] != "bearing":
            print(f"  Skipping extraction — unsupported category.")
            continue

        result = extract_fields(raw_text)
        output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"  Saved to {output_path}")
