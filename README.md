# IEEE TechRush
# OCR-Based MCQ Generator using Tesseract & Groq (LLaMA3)

This project extracts text from a PDF using **Tesseract OCR** and generates **Multiple Choice Questions (MCQs)** using the **LLaMA3 model** via the **Groq API**. It allows users to convert educational content from PDFs (like NCERT textbooks) into quiz questions automatically.

---

## Features

- Extracts text from images using `pytesseract`
- Uses LLaMA3 (`llama3-8b-8192`) to generate MCQs
- Allows user to specify question count and difficulty
- Command-line interface for quick interaction

---

## Tech Stack

- Python
- Tesseract OCR
- Groq API (LLaMA3)
- dotenv (`.env` support for API key)

---

## Project Structure

---

# Installation
First install [Tesseract OCR Engine](https://github.com/tesseract-ocr/tesseract) and make sure to include it in your PATH.
## **Linux**:
```
git clone https://github.com/manmeetsantre/IEEE_TechRush.git
cd IEEE_TechRush
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```
## **Windows**:

