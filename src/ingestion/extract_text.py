import pymupdf # PyMuPDF
import os # To make the filesystem easier

def extract_pdf(pdf_path):
	doc = pymupdf.open(pdf_path)
	text = ""
	for page in doc:
		text += page.get_text()
	doc.close()
	return text


if __name__ == "__main__":
	script_dir = os.path.dirname(os.path.abspath(__file__))
	project_root = os.path.join(script_dir, "..", "..")
	pdf_path = os.path.join(project_root, "data", "raw", "skf_6205.pdf")
	text = extract_pdf(pdf_path)
	print(text)

    
