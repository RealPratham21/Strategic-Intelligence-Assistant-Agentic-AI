from docling.document_converter import DocumentConverter
from langchain_core.tools import tool
import os

@tool
def read_pdf_document(file_path: str):
    """
    Converts a local PDF file into structured Markdown. 
    Use this when a user provides a file or refers to a local document.
    """
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    
    try:
        # DocumentConverter handles the heavy lifting of OCR and table extraction
        converter = DocumentConverter()
        result = converter.convert(file_path)
        return result.document.export_to_markdown()
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"