from pytesseract import pytesseract
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class OCR:    
    def __init__(self):
        self.path = r"/usr/bin/tesseract"
    
    def extract(self, filename): 
        try:
            pytesseract.tesseract_cmd = self.path

            text = pytesseract.image_to_string(filename)

            return text
        except Exception as e:
            print(e)
            return "Error"
    
    def mcqs_generation(self, text):
        try:
            count = int(input("Enter number of mcqs you wish: "))
            difficulty = input("Enter the difficulty level for questions: ")
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f" {text} use this content and give me {count} mcqs of {difficulty} difficulty  in json format ",
                    }
                ],
                model="llama3-8b-8192",
            )

            print(chat_completion.choices[0].message.content)

        except Exception as e:
            print(f"An error occurred: {e}")

ocr = OCR()
text = ocr.extract("ncert-1.png")
ocr.mcqs_generation(text)
