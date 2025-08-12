# Necessary imports
from flask import Flask, request, jsonify, render_template, send_file
import tempfile
from reportlab.lib import colors  # used for PDF generation
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
import wave
from piper import PiperVoice
from bs4 import BeautifulSoup
import re

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
load_dotenv()

latest_summary = ""
latest_mcqs = ""
topicsExtracted = False # to keep track of topic extraction state

app = Flask(__name__, template_folder='templates')
CORS(app)  # allows requests from other origins (frontend)

# setup Gemini model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-2.0-flash')
eng_voice = PiperVoice.load("en_US-lessac-high.onnx")
hin_voice = PiperVoice.load("hi_IN-pratham-medium.onnx")

def ishindi(text):
    return any('\u0900' <= char <= '\u097F' for char in text)

def generate_with_ollama(prompt):
    try:
        url = "http://localhost:11434/api/generate"
        print("Generating with Mistral (Ollama)...")

        payload = {
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    except Exception as e:
        print(f"Ollama connection error: {e}")
        return None

def generate_with_gemini(prompt):
    try:
        print("Generating with Gemini...")
        response = gemini_model.generate_content(
            contents=prompt,
            generation_config={'response_mime_type': 'application/json'}
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return None
 
@app.route('/', methods=['POST', 'GET'])
def home():
    global latest_summary, latest_mcqs, topicsExtracted
    if request.method == 'POST':
        start_time = time.time()

        # get uploaded file and form inputs
        pdf_file = request.files.get('pdf_file')
        count = int(request.form.get('question_count', 5))
        difficulty = request.form.get('difficulty', 'Medium')
        topic = request.form.get('topic', 'All')
        provider = request.form.get('provider', 'gemini')

        if not pdf_file:
            return jsonify({"error": "No PDF file provided"}), 400

        # extract text from PDF
        extract_start = time.time()
        text, method = extract_text_from_pdf(pdf_file)
        extract_time = time.time() - extract_start
        print(f"Extraction took {extract_time} seconds")
        
        if not text.strip():
            return jsonify({"error": "No text extracted from PDF"}), 400

        # run based on whether topics have been extracted
        if not topicsExtracted:
            topicsExtracted = True
            topic_extraction_start = time.time()
            topics = topic_extraction(text)
            topic_extraction_time = time.time() - topic_extraction_start
            print(f"Topic extraction took {topic_extraction_time} seconds")
            return jsonify({"topics": topics})
        else:
            topicsExtracted = False
            # generate summary
            summary_start = time.time()
            summarized_text = summary(text)
            summary_time = time.time() - summary_start
            print(f"Summarization took {summary_time} seconds")

            # generate MCQs
            mcq_start = time.time()
            mcqs = generate_mcqs(text, count=count, difficulty=difficulty, topic=topic, provider=provider)
            mcq_time = time.time() - mcq_start
            print(f"MCQ generation took {mcq_time} seconds")

            total_time = time.time() - start_time

            latest_summary = summarized_text
            latest_mcqs = mcqs

            # send final response
            return jsonify({
                "summary": summarized_text,
                "mcqs": mcqs,
                "metadata": {
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_count": count,
                    "extraction_method": method,
                    "provider": provider
                },
                "timing": {
                    "extraction_time": f"{extract_time:.2f}s",
                    "summary_time": f"{summary_time:.2f}s",
                    "mcq_time": f"{mcq_time:.2f}s",
                    "total_time": f"{total_time:.2f}s"
                }
            })
    else:
        # resetting the flag whenever user reloads (GET request)
        topicsExtracted = False
    return render_template('index.html')

@app.route('/download/pdf', methods=['GET'])
def download_pdf():
    if not latest_summary and not latest_mcqs:
        return "No data to download", 400
    
    try:
        mcq_list = json.loads(latest_mcqs)
    except:
        mcq_list = []

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_file.name)
    styles = getSampleStyleSheet()

    # Custom styles
    question_style = ParagraphStyle('QuestionStyle', parent=styles['BodyText'], spaceAfter=6, fontSize=11, leading=14)
    answer_style = ParagraphStyle('AnswerStyle', parent=styles['BodyText'], textColor=colors.green, spaceAfter=12)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading1'], spaceAfter=12)

    elements = []

    # Summary
    elements.append(Paragraph("📄 Summary", heading_style))
    elements.append(Paragraph(latest_summary, styles['BodyText']))
    elements.append(Spacer(1, 15))

    # MCQs
    elements.append(Paragraph("📝 Multiple Choice Questions", heading_style))
    for i, mcq in enumerate(mcq_list, start=1):
        elements.append(Paragraph(f"{i}. {mcq['question']}", question_style))

        # Bullet list for options
        option_items = [
            ListItem(Paragraph(f"{chr(65+idx)}. {opt}", styles['BodyText']), bulletColor=colors.black)
            for idx, opt in enumerate(mcq['options'])
        ]
        elements.append(ListFlowable(option_items, bulletType='bullet', start='circle'))

        # Correct Answer
        correct_opt = f"{chr(65+mcq['correctAnswer'])}. {mcq['options'][mcq['correctAnswer']]}"
        elements.append(Paragraph(f"✅ Correct Answer: <b>{correct_opt}</b>", answer_style))

        # Explanation
        elements.append(Paragraph(f"ℹ {mcq['explanation']}", styles['BodyText']))
        elements.append(Spacer(1, 12))

    doc.build(elements)
    return send_file(temp_file.name, as_attachment=True, download_name="results.pdf")

@app.route('/download/txt', methods=['GET'])
def download_txt():
    if not latest_summary and not latest_mcqs:
        return "No data to download", 400

    # Remove HTML from summary
    clean_summary = BeautifulSoup(latest_summary, "html.parser").get_text()

    try:
        mcq_list = json.loads(latest_mcqs)
    except:
        mcq_list = []

    content = "📄 Summary\n" + clean_summary + "\n\n📝 Multiple Choice Questions\n"
    for i, mcq in enumerate(mcq_list, start=1):
        content += f"{i}. {mcq['question']}\n"
        for idx, opt in enumerate(mcq['options']):
            content += f"   {chr(65+idx)}. {opt}\n"
        content += f"✅ Correct Answer: {chr(65+mcq['correctAnswer'])}. {mcq['options'][mcq['correctAnswer']]}\n"
        content += f"ℹ Explanation: {mcq['explanation']}\n\n"

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8')
    temp_file.write(content)
    temp_file.close()
    return send_file(temp_file.name, as_attachment=True, download_name="results.txt")


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
        if len(text.strip())/len(reader.pages) > 50:
            print("[INFO] Used pypdf for text extraction.")
            return text, "pypdf"
    except Exception as e:
        print(f"[WARN] pypdf failed: {e}")

    # fallback: use OCR on image version of PDF
    print("[INFO] Falling back to OCR with pytesseract.")
    images = convert_from_bytes(pdf_bytes, dpi=75, grayscale=True)
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image)
    return text, "ocr"

def topic_extraction(text):
    prompt = f"""You are tasked with summarizing educational content. Identify around 10 key educational themes from the provided text. 
    Guidelines:

    Each theme should be a concise noun phrase (maximum 3 words, maximum 20 characters).
    No explanations, examples, quotes, or brackets.
    Avoid vague terms (e.g., "things", "concepts", "nature").
    Ensure no repetition or topic titles.
    Topic tagging must follow the specified instructions:
    * the topic must not be too generic (i.e. Science, Engineering, etc.)
    * the topic must not be too specific (i.e. Proof-Of-Work, Merkle Tree, etc.)
    * the topic must be such that one can get a good amount of questions belonging to a certain topic, such that the topics can be later filtered by the user
    * the topics must be such that they can be used to tag questions later
    * preserve the language (like if the text is in Hindi, the topics must be in Hindi too)

Output format (JSON array of strings):
[
"Topic A",
"Topic B"
...
]

Text:
"{text}"
"""
    response_topics = gemini_model.generate_content(
            contents=prompt,
            generation_config={'response_mime_type': 'application/json'}
    )
    return response_topics.text

# sends summary request to local Mistral (Ollama) API
def summary(text):
    prompt = f"Please create the summary for following text: {text}.\nDirectly begin with summary. Make it readable by a common user, making the PDF simple to understand. You can also use markdown to make it visually appealing. However make sure it remains formal in nature, do not be too casual/informal. Also make sure the summary is concise, do not make it too long. Make sure to retain the language of the text. That is, if the text is in Hindi, keep your response in Hindi too. Try to use markdown as much as possible. Use formatting techniques like giving proper heading format to title, bullet points, etc. to make it look visually appealing."
    response_text = markdown(gemini_model.generate_content(contents=prompt).text)
    voice = hin_voice if ishindi(text) else eng_voice
    audio_path = os.path.join(STATIC_FOLDER, "audio.wav")
    with wave.open(audio_path, "wb") as wav_file:
        voice.synthesize_wav(BeautifulSoup(response_text, 'html.parser').get_text(), wav_file)
    # markdown makes the summary display better on frontend
    return response_text

# uses Gemini to generate MCQs in JSON format
def generate_mcqs(text, count, difficulty, topic, provider):
    batch_size = 100
    final_response = ""

    for i in range(0, count, batch_size):
        print("[INFO] Generating MCQs batch:", i + 1)
        batch_count = min(batch_size, count - i)

        # detailed instruction to force Gemini to return pure JSON
        error_messages = []
        mcqs = []
        prompt = f"""
Create {batch_count} multiple choice questions based on this text extracted from PDF:\n\n{text}
Requirements:
- difficulty: {difficulty}
- topics: {topic}
- each question must have:
  * clear question stem
  * correct answer (specify the number, that is, 0-3)
  * concise explanation
  * difficulty rating
  * topic tag
  * create mcqs of single answer and true false type questions.
  * also create fill in the blanks type questions and match the following type questions.
  *  for single correct questions or other questions,  give 
  "question type": "single_correct" or "true_false" or "fill_in_the_blanks" or "match_the_following" for this 
  this should be the starting of the question. 
- format the output as a JSON array of objects, each with:
- "question": the question text
- "options": an array of 4 options (A, B, C, D)
- "correctAnswer": index of the correct option (0-3)
- "explanation": why the correct answer is correct
- "topic": relevant topic that the question belongs to
- "question type": the type of question, which can be "single_correct", "true_false", "fill_in_the_blanks", or "match_the_following"
  * Only one of the 4 options should be correct
- Every question must have 4 options (A, B, C, D) in the JSON "options" field
- Make sure to preserve the language of the original PDF text (e.g., Hindi stays Hindi)
- If topic = 'All', you can choose appropriate topics yourself, but do not set every topic as "All"
- Final output must be in pure JSON format:

- options must be concise and relevant to the question
- make sure to preserve the language of the text extracted from PDF, that is, if the text is in Hindi, your response must be in Hindi too
- make sure that the generated topics are as given above, that is, the generated questions must belong to topics: {topic}
- the only exception to the above rule is when the given topic {topic} is 'All', in which case you can craft your own topics.
- If {topic} is equal to 'All', then you must craft your own topics. Do not make every question's topic as All.
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

    print(f"Prompt length: {len(prompt)} characters")
    
    try:
        print(f"Using provider: {provider}")
        if provider.startswith('ollama'):
            response_text = generate_with_ollama(prompt)
        else:  # Default to Gemini
            response_text = generate_with_gemini(prompt)
            
        if not response_text:
            error_messages.append("Provider returned empty response")
            return json.dumps([])
            
        print(f"Raw response ({len(response_text)} chars): {response_text[:200]}...")

        # Clean response - remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        # Remove any text outside JSON brackets
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
            
        # Try direct JSON parse
        try:
            mcqs = json.loads(response_text)
            if not isinstance(mcqs, list):
                error_messages.append("Response is not a JSON array")
                mcqs = []
        except json.JSONDecodeError as e:
            error_messages.append(f"JSON parse error: {e}")
            print(f"Invalid JSON: {response_text[:500]}")
            
    except Exception as e:
        error_messages.append(f"Unexpected error: {e}")
        print(f"Exception: {str(e)}")
    
    # Validate and add IDs to MCQs
    valid_mcqs = []
    for idx, mcq in enumerate(mcqs):
        if not isinstance(mcq, dict):
            continue
            
        # Ensure all required fields exist
        required_keys = ['question', 'options', 'correctAnswer', 'explanation']
        if all(key in mcq for key in required_keys):
            mcq['id'] = idx + 1
            
            # Ensure correctAnswer is integer
            if isinstance(mcq['correctAnswer'], str):
                try:
                    mcq['correctAnswer'] = int(mcq['correctAnswer'])
                except ValueError:
                    mcq['correctAnswer'] = 0
            
            if 'topic' not in mcq or not str(mcq['topic']).strip():
                mcq['topic'] = topic
                
            valid_mcqs.append(mcq)
    
    # If we got fewer questions than requested
    if len(valid_mcqs) < count:
        error_messages.append(f"Only got {len(valid_mcqs)}/{count} valid MCQs")
    
    if error_messages:
        print(f"MCQ generation completed with errors: {', '.join(error_messages)}")
    
    return json.dumps(valid_mcqs)

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
