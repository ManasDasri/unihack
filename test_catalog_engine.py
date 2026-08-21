import json
import os
import sys

from src.pipeline.process_product import ProductPipeline
from src.retrieval.document_index import DocumentIndex
from groq import Groq

def run_test():
    client = Groq()
    index = DocumentIndex()
    
    # Shared DocumentIndex with both PDFs
    index.add_pdf("data/raw/skf_6201.pdf")
    index.add_pdf("data/raw/skf_6205.pdf")
    
    schema_dir = "data/schema"
    
    # Load products
    with open("data/extracted/skf_6201.json", "r") as f:
        product_6201 = json.load(f)
        
    with open("data/extracted/skf_6205.json", "r") as f:
        product_6205 = json.load(f)
        
    # Remove material from both to force corpus enrichment
    if "material" in product_6201.get("attributes", {}):
        del product_6201["attributes"]["material"]
        
    if "material" in product_6205.get("attributes", {}):
        del product_6205["attributes"]["material"]

    # Process 6201
    pipeline_6201 = ProductPipeline(
        schema_dir=schema_dir,
        pdf_path="data/raw/skf_6201.pdf",
        document_index=index,
        groq_client=client,
    )
    result_6201 = pipeline_6201.process(product_6201)
    
    # Process 6205
    pipeline_6205 = ProductPipeline(
        schema_dir=schema_dir,
        pdf_path="data/raw/skf_6205.pdf",
        document_index=index,
        groq_client=client,
    )
    result_6205 = pipeline_6205.process(product_6205)
    
    # Verifications
    failures = []
    
    # 6201 Check
    mat_6201 = result_6201["product"]["attributes"].get("material")
    
    if not mat_6201:
        failures.append("6201 material not populated")
    else:
        # Check provenance from corpus_enrichment array
        enrichment_6201 = next((e for e in result_6201["corpus_enrichment"] if e["field"] == "material"), None)
        if not enrichment_6201:
            failures.append("6201 material corpus enrichment missing")
        elif enrichment_6201.get("source") != "skf_6201.pdf":
            failures.append(f"6201 got wrong evidence source: {enrichment_6201.get('source')}")
        
    if result_6201["decision"] != "verified":
        failures.append("6201 decision is not verified")
        
    # 6205 Check
    mat_6205 = result_6205["product"]["attributes"].get("material")
    
    if not mat_6205:
        failures.append("6205 material not populated")
    else:
        # Check provenance from corpus_enrichment array
        enrichment_6205 = next((e for e in result_6205["corpus_enrichment"] if e["field"] == "material"), None)
        if not enrichment_6205:
            failures.append("6205 material corpus enrichment missing")
        elif enrichment_6205.get("source") != "skf_6205.pdf":
            failures.append(f"6205 got wrong evidence source: {enrichment_6205.get('source')}")
        
    if result_6205["decision"] != "verified":
        failures.append("6205 decision is not verified")
        
    if failures:
        print("TEST FAILED")
        for f in failures:
            print("-", f)
        sys.exit(1)
        
    print("TEST PASSED")

if __name__ == "__main__":
    run_test()
