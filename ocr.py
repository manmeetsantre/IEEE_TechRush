# Program for OCR functionality using tesseract - extracting text from PDFs

from pdf2image import convert_from_bytes
import pytesseract

def extract_text(file):
    """
        Extract text from PDF

        Input:
        file - bytes

        Output:
        text - string
    """
    try:
        pages = convert_from_bytes(file)
        text = ""
        # Adding page numbers
        for i, page in enumerate(pages):
            pagetext = pytesseract.image_to_string(page)
            text += f"\n\n--- Page {i+1} ---\n{pagetext}"
        return text

    except Exception as e:
            return f"Error during extracting text: {str(e)}"
