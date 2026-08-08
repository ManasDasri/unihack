import os
import json
from dotenv import load_dotenv
load_dotenv() 
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, "..", "..")
categories_path = os.path.join(project_root, "data","schema","categories.json")

def load_categories():
    with open(categories_path, "r") as f:
        return json.load(f)["supported_categories"]

def classify_category(raw_text):
    categories = load_categories()
    prompt = f"""
    You are classifying an industrial product document into a category.

    Supported categories: {categories}

    Document text:
    {raw_text}

    Look at the actual product being described (not just the filename or page title). 
    Return ONLY valid JSON in this exact format, no explanation:
    {{
    "category": "one of the supported categories, or 'unsupported' if none match",
    "confidence": "high, medium, or low",
    "reasoning": "one short sentence explaining why"
}}
"""
    response = client.chat.completion.create(
        model= "llama3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw_output = response.choices[0].message.content
    cleaned = raw_output.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)

