# Program for extracting text from PDFs - optionally using OCR

import pypdf
from pdf2image import convert_from_bytes
import pytesseract
import io

def extract_text(file):
    """
        Extract text from PDF. Extract text directly using pypdf if text is selectable otherwise use OCR

        Input:
        file - bytes

        Output:
        text - string
    """
    try:
        file_stream = io.BytesIO(file)
        pdf_reader = pypdf.PdfReader(file_stream)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text() or ""
            text += page_text
        if text.strip():
            return text
        else:
            pages = convert_from_bytes(file, dpi=75, grayscale=True)
            ocr_text = ""
            for i, page in enumerate(pages):
                page_text = pytesseract.image_to_string(page)
                ocr_text += f"--- Page {i + 1} ---\n{page_text}\n\n"
            return ocr_text
    except Exception as e:
        return f"Error: {str(e)}"
