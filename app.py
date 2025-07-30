from flask import Flask, render_template, request, jsonify
from pytesseract import pytesseract
from groq import Groq
from dotenv import load_dotenv
import os
import time
from pdf2image import convert_from_bytes
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf):
    try:
        pages = convert_from_bytes(pdf, dpi=150, grayscale=True)  # Lower DPI for speed
        text = ""

        with ThreadPoolExecutor() as executor:
            results = list(executor.map(pytesseract.image_to_string, pages))

        for i, pagetext in enumerate(results):
            text += f"\n\n--- Page {i+1} ---\n{pagetext}"

        return text
    except Exception as e:
        return f"Error during extracting text: {str(e)}"

def generate_mcqs(text, count, difficulty, msg):
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{text}\n\nGenerate {count} MCQs of {difficulty} difficulty in well formatted JSON should be readable.   this is the custom message from user {msg}",
                }
            ],
            model="llama3-8b-8192",
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq Error: {e}")
        return jsonify({"error": "Failed to generate MCQs"}), 500

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf = request.files["pdf"]
        count = request.form["count"]
        difficulty = request.form["difficulty"]
        msg = request.form["msg"]

        if pdf:
            timestart = time.time()
            extracted_text = extract_text_from_pdf(pdf.read())
            print(f"Text extraction time: {time.time() - timestart} seconds")

            timestart = time.time()
            mcqs_json = generate_mcqs(extracted_text, count, difficulty, msg)
            print(f"MCQ generation time: {time.time() - timestart} seconds")

            return jsonify({"mcqs": mcqs_json})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
