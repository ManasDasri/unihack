import os
import json
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SCRIPT_DIR, "..", "..")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "data", "schema", "bearing.json")

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
    from src.ingestion.extract_text import extract_pdf  # reuse your existing function

    pdf_path = os.path.join(PROJECT_ROOT, "data", "raw", "skf_6205.pdf")
    raw_text = extract_pdf(pdf_path)
    result = extract_fields(raw_text)
    print(json.dumps(result, indent=2))