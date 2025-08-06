from flask import Flask, request, jsonify, render_template
from pytesseract import pytesseract
from dotenv import load_dotenv
import os
from pdf2image import convert_from_bytes
import time
import google.generativeai as genai
import requests  
from groq import Groq
from pypdf import PdfReader

load_dotenv()

app = Flask(__name__, template_folder='templates')
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        start_time = time.time()
        
        # Get form data
        pdf_file = request.files.get('pdf_file')
        count = int(request.form.get('question_count', 5))
        difficulty = request.form.get('difficulty', 'medium')
        chapter = request.form.get('chapter', 'General')
        topic = request.form.get('topic', 'General')
        
        if not pdf_file:
            return jsonify({"error": "No PDF file provided"}), 400
        
        extract_start = time.time()
        text, method = extract_text_from_pdf(pdf_file)
        extract_time = time.time() - extract_start
        
        if not text.strip():
            return jsonify({"error": "No text extracted from PDF"}), 400
        
        summary_start = time.time()
        summary = extractive_summary(text)
        summary_time = time.time() - summary_start
        
        mcq_start = time.time()
        mcqs = generate_mcqs(summary, count=count, difficulty=difficulty, 
                             chapter=chapter, topic=topic)
        mcq_time = time.time() - mcq_start
        
        total_time = time.time() - start_time
        
        return jsonify({
            "summary": summary,
            "mcqs": mcqs,
            "metadata": {
                "chapter": chapter,
                "topic": topic,
                "difficulty": difficulty,
                "question_count": count,
                "extraction_method": method
            },
            "timing": {
                "extraction_time": f"{extract_time:.2f}s",
                "summary_time": f"{summary_time:.2f}s",
                "mcq_time": f"{mcq_time:.2f}s",
                "total_time": f"{total_time:.2f}s"
            }
        })
    
    return render_template('index.html')

def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()  # read once
    text = ''
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        if len(text.strip()) > 100:
            print("[INFO] Used pypdf for text extraction.")
            return text, "pypdf"
    except Exception as e:
        print(f"[WARN] pypdf failed: {e}")
    
    print("[INFO] Falling back to OCR with pytesseract.")
    images = convert_from_bytes(pdf_bytes)
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image)
    return text, "ocr"

import io

def extractive_summary(text):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Please create the extractive summary for following text: {text} directly begin with summary, keep important events, and keywords for creating mcqs later"}
        ]
    )
    return response.choices[0].message.content[:3000]  # Limit to prevent token overload

def generate_mcqs(text, count, difficulty, chapter, topic):
    total_mcqs = ""
    batch_size = 10  # safer to chunk in batches

    for i in range(0, count, batch_size):
        batch_count = min(batch_size, count - i)
        prompt = f"""Create {batch_count} multiple choice questions based on this summary:\n\n{text}

Requirements:
- Difficulty: {difficulty}
- Chapter: {chapter}
- Topic: {topic}
- Each question must have:
  * Clear question stem
  * 4 options (A-D)
  * Correct answer (specify letter)
  * Concise explanation
  * Difficulty rating
  * Topic tag
  * Chapter reference

Format:
Q1. [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
---
Correct Answer: [Letter]
Explanation: [Explanation]
Topic: [Topic]
Difficulty: [Rating]
Chapter: [Chapter]
"""

        try:
            response = gemini_model.generate_content(prompt)
            total_mcqs += response.text + "\n\n"
        except Exception as e:
            print(f"[ERROR] Gemini failed: {e}")
            total_mcqs += f"\n[ERROR generating batch {i+1}-{i+batch_count}]: {str(e)}\n"

    return total_mcqs.strip()

@app.route('/network-test')
def network_test():
    test_urls = {
        "Google Generative AI": "https://generativelanguage.googleapis.com",
        "Tesseract OCR": "https://github.com/tesseract-ocr/tesseract",
    }
    
    results = {}
    for service, url in test_urls.items():
        try:
            response = requests.get(url, timeout=5)
            results[service] = {
                "status": "success" if response.status_code == 200 else f"HTTP {response.status_code}",
                "url": url
            }
        except Exception as e:
            results[service] = {
                "status": "error",
                "error": str(e),
                "url": url
            }
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
