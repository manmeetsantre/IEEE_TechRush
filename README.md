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
```

### **Windows**:
####  Step 1: Install Tesseract OCR

1. Download the latest Windows installer from:
    [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)  
   (File name: `tesseract-ocr-w64-setup-5.5.0.20241111.exe`)

2. Run the installer:
   -  Note the installation path (e.g., `C:\Program Files\Tesseract-OCR`)
   -  Check the option to **add Tesseract to system PATH**

3. If you didn't add it to PATH during install:
   - Go to **System Properties > Environment Variables**
   - Edit the `Path` variable and add:
     ```
     C:\Program Files\Tesseract-OCR
     ```
---
####  Step 2: Clone and Set Up the Project

```bash
:: Clone the repository
git clone https://github.com/manmeetsantre/IEEE_TechRush.git
cd IEEE_TechRush

:: (Optional) Initialize a virtual environment
python -m venv venv

:: Activate the virtual environment
venv\Scripts\activate

:: Install required packages
pip install -r requirements.txt
```

###  Setting Up Environment Variables (`.env`)

This project uses a `.env` file to load your **Groq API key** securely without exposing it in the code.

####  Steps to Set It Up

1. In the project root directory, create a file named `.env`
2. Add the following line inside it:

GROQ_API_KEY= {your_actual_groq_api_key_here}

>  Replace `your_actual_groq_api_key_here` with your API key from [https://console.groq.com/keys](https://console.groq.com/keys)

---

####  How It Works

The project uses the `python-dotenv` library to load environment variables from the `.env` file.  
Inside the code, it accesses the key like this:

```python
import os
api_key = os.getenv("GROQ_API_KEY")
```
This keeps your API credentials secure and separated from the source code.
