from flask import Flask, request, jsonify, render_template
from pytesseract import pytesseract
from dotenv import load_dotenv
import os
from pdf2image import convert_from_bytes
import time
import requests  
from groq import Groq
from pypdf import PdfReader
import io

load_dotenv()

app = Flask(__name__, template_folder='templates')
client_summary = Groq(api_key=os.getenv("GROQ_API_KEY_SUMMARY"))
client_mcq = Groq(api_key=os.getenv("GROQ_API_KEY_MCQ"))

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        start_time = time.time()
        pdf_file = request.files.get('pdf_file')
        count = int(request.form.get('question_count', 5))
        difficulty = request.form.get('difficulty', 'medium')
        chapter = request.form.get('chapter', 'General')
        
        if not pdf_file:
            return jsonify({"error": "No PDF file provided"}), 400
        
        extract_start = time.time()
        text, method = extract_text_from_pdf(pdf_file)
        extract_time = time.time() - extract_start
        
        if not text.strip():
            return jsonify({"error": "No text extracted from PDF"}), 400
        
        summary_start = time.time()
        summarized_text = summary(text)
        summary_time = time.time() - summary_start
        
        mcq_start = time.time()
        mcqs = generate_mcqs(text, count=count, difficulty=difficulty, 
                             chapter=chapter)
        mcq_time = time.time() - mcq_start
        
        total_time = time.time() - start_time
        
        return jsonify({
            "summary": summarized_text,
            "mcqs": mcqs,
            "metadata": {
                "chapter": chapter,
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

def summary(text):
    response_summary = client_summary.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a content summarizer."},
            {"role": "user", "content": f"Please create the summary for following text: {text} directly begin with summary, keep important events, and keywords for creating mcqs later"}
        ]
    )
    return response_summary.choices[0].message.content[:5000]  # Limit to prevent token overload

def generate_mcqs(text, count, difficulty, chapter):
    batch_size = 10  # safer to chunk in batches
    final_response = ""
    for i in range(0, count, batch_size):
        print("[INFO] Generating MCQs batch:", i + 1)
        batch_count = min(batch_size, count - i)
        prompt = f"""
Create {batch_count} multiple choice questions based on this summary:\n\n{text}
Requirements:
- difficulty: {difficulty}
- chapter: {chapter}
- each question must have:
  * clear question stem
  * 4 options (a-d)
  * correct answer (specify letter)
  * concise explanation
  * difficulty rating
  * topic tag
  * chapter reference
- the format must be in json, as specified below:
[
    {{
        "question": "question here",
        "options": ["option1", "option2", "option3", "option4"],
        "correctAnswer": "option which is correct",
        "explanation": "explanation why correctAnswer is correct",
        "topic": "relevant topic that the question belongs to"
    }},
    ...
]
PLEASE PLEASE PLEASE MAKE IT IN JSON ONLY. DO NOT GIVE ANY EXTRA TEXT IN THE BEGINNING OR IN THE END. I HAVE TO PARSE THE JSON THAT IS GIVEN BY YOU FURTHER. SO PLEASE ONLY GIVE JSON. PLEASE GIVE JSON ONLY. GIVE JSON FORMAT ONLY. DO NOT WRITE ANYTHING ELSE. DO NOT PUT NEWLINES OR ANYTHING WHICH IS NOT IN JSON FORMAT."""

        response_mcqs = client_mcq.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a mcq generator"},
            {"role": "user", "content": prompt}
        ])
        final_response += response_mcqs.choices[0].message.content
    return final_response


if __name__ == '__main__':
    app.run(debug=True)
