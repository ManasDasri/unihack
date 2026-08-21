import json
import os

from flask import Flask, jsonify, request
from dotenv import load_dotenv
from groq import Groq

from src.pipeline.process_product import ProductPipeline
from src.retrieval.document_index import DocumentIndex

load_dotenv()

app = Flask(__name__, static_folder="frontend", static_url_path="")

DATA_EXTRACTED = os.path.join("data", "extracted")
DATA_RAW = os.path.join("data", "raw")
SCHEMA_DIR = os.path.join("data", "schema")

PRODUCTS = {
    "skf_6205": {
        "label": "SKF 6205",
        "extracted": os.path.join(DATA_EXTRACTED, "skf_6205.json"),
        "pdf": os.path.join(DATA_RAW, "skf_6205.pdf"),
    },
    "skf_6201": {
        "label": "SKF 6201",
        "extracted": os.path.join(DATA_EXTRACTED, "skf_6201.json"),
        "pdf": os.path.join(DATA_RAW, "skf_6201.pdf"),
    },
}

_shared_index = None


def get_shared_index():
    global _shared_index
    if _shared_index is None:
        _shared_index = DocumentIndex()
        for cfg in PRODUCTS.values():
            _shared_index.add_pdf(cfg["pdf"])
    return _shared_index


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/products")
def list_products():
    return jsonify([
        {"id": pid, "label": cfg["label"]}
        for pid, cfg in PRODUCTS.items()
    ])


@app.route("/api/process", methods=["POST"])
def process_product():
    body = request.get_json(force=True)
    product_id = body.get("product_id")
    contaminate_with = body.get("contaminate_with")

    if product_id not in PRODUCTS:
        return jsonify({"error": "Unknown product"}), 400

    cfg = PRODUCTS[product_id]

    with open(cfg["extracted"], "r") as f:
        product = json.load(f)

    if contaminate_with and contaminate_with in PRODUCTS:
        wrong_index = DocumentIndex()
        wrong_index.add_pdf(PRODUCTS[contaminate_with]["pdf"])
        index = wrong_index
    else:
        index = get_shared_index()

    client = Groq()

    pipeline = ProductPipeline(
        schema_dir=SCHEMA_DIR,
        pdf_path=cfg["pdf"],
        document_index=index,
        groq_client=client,
    )

    result = pipeline.process(product)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, port=5050)
