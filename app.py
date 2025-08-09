# Necessary imports
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS  # handles cross-origin issues during frontend-backend connection
from pytesseract import pytesseract  # used for OCR if PDF is image-based
from dotenv import load_dotenv  # loads environment variables like API keys
import os
from pdf2image import convert_from_bytes  # converts PDF pages to images
import time  # used to measure execution time
import requests  # for sending HTTP requests (used for Mistral)
import google.generativeai as genai  # Gemini API
from pypdf import PdfReader  # extracts text from normal (text-based) PDFs
import io
from markdown import markdown  # to render summary in markdown
import json
import random
import string

load_dotenv()

app = Flask(__name__, template_folder='templates')
CORS(app)  # allows requests from other origins (frontend)

# setup Gemini model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# generates a random string (used for unique IDs if needed)
def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        start_time = time.time()

        # get uploaded file and form inputs
        pdf_file = request.files.get('pdf_file')
        count = int(request.form.get('question_count', 5))
        difficulty = request.form.get('difficulty', 'Medium')
        chapter = request.form.get('chapter', 'All')
        
        if not pdf_file:
            return jsonify({"error": "No PDF file provided"}), 400

        # extract text from PDF
        extract_start = time.time()
        text, method = extract_text_from_pdf(pdf_file)
        extract_time = time.time() - extract_start
        
        if not text.strip():
            return jsonify({"error": "No text extracted from PDF"}), 400

        # generate summary
        summarized_text, summary_time = summary(text)

        # generate MCQs
        mcq_start = time.time()
        mcqs = generate_mcqs(text, count=count, difficulty=difficulty, chapter=chapter)
        mcq_time = time.time() - mcq_start

        total_time = time.time() - start_time

        # send final response
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

# tries to extract text using pypdf, falls back to OCR if text not found
def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()
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

    # fallback: use OCR on image version of PDF
    print("[INFO] Falling back to OCR with pytesseract.")
    images = convert_from_bytes(pdf_bytes, dpi=75, grayscale=True)
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image, lang='eng+hin+mar', config='--psm 6')
    return text, "ocr"

# sends summary request to local Mistral (Ollama) API
def summary(text):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    prompt = f"Please create the summary for following text: {text}.\nDirectly begin with summary. Make it readable by a common user, making the PDF simple to understand. You can also use markdown to make it visually appealing. However make sure it remains formal in nature, do not be too casual/informal. Also make sure the summary is concise, do not make it too long. Make sure to retain the language of the text. That is, if the text is in Hindi, keep your response in Hindi too. Try to use markdown as much as possible. Use formatting techniques like giving proper heading format to title, bullet points, etc. to make it look visually appealing."
    data = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post('http://localhost:11434/api/generate',
                             headers=headers,
                             data=json.dumps(data))
    
    # markdown makes the summary display better on frontend
    return markdown(response.json().get('response', 'Error: No response field found')), response.json().get('total_duration', -1000)

# uses Gemini to generate MCQs in JSON format
def generate_mcqs(text, count, difficulty, chapter):
    batch_size = 100
    final_response = ""

    for i in range(0, count, batch_size):
        print("[INFO] Generating MCQs batch:", i + 1)
        batch_count = min(batch_size, count - i)

        # detailed instruction to force Gemini to return pure JSON
        prompt = f"""
Create {batch_count} multiple choice questions based on this text extracted from PDF:\n\n{text}
Requirements:
- difficulty: {difficulty}
- chapter: {chapter}
- each question must have:
  * clear question stem
  * 4 options
  * correct answer (specify the number, that is, 0-3)
  * concise explanation
  * difficulty rating
  * topic tag
- topic tagging must follow the specified instructions:
  * the topic must not be too generic (i.e. Science, Engineering, etc.)
  * the topic must not be too specific (i.e. Proof-Of-Work, Merkle Tree, etc.)
  * the topic must be such that one can get a good amount of questions belonging to a certain topic, such that the topics can be later filtered by the user
- make sure to preserve the language of the text extracted from PDF, that is, if the text is in Hindi, your response must be in Hindi too
- the format must be in json, as specified below:
[
    {{
        "question": "question here",
        "options": ["option1", "option2", "option3", "option4"],
        "correctAnswer": "number of answer which is correct, that is, from 0 to 3. make sure to start from 0.",
        "explanation": "explanation why correctAnswer is correct",
        "topic": "relevant topic that the question belongs to"
    }},
    ...
]
PLEASE PLEASE PLEASE MAKE IT IN JSON ONLY. DO NOT GIVE ANY EXTRA TEXT IN THE BEGINNING OR IN THE END. I HAVE TO PARSE THE JSON THAT IS GIVEN BY YOU FURTHER. SO PLEASE ONLY GIVE JSON. PLEASE GIVE JSON ONLY. GIVE JSON FORMAT ONLY. DO NOT WRITE ANYTHING ELSE. DO NOT PUT NEWLINES OR ANYTHING WHICH IS NOT IN JSON FORMAT."""

        response_mcqs = gemini_model.generate_content(
            contents=prompt,
            generation_config={'response_mime_type': 'application/json'}
        )

        final_response += response_mcqs.text

    # load and clean up final JSON output
    final_response_json = json.loads(final_response)
    for idx, val in enumerate(final_response_json):
        if isinstance(val['correctAnswer'], str):
            val['correctAnswer'] = int(val['correctAnswer'])
        val.update({'id': idx+1})  # add ID to each MCQ
    print(final_response_json)
    return json.dumps(final_response_json)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
