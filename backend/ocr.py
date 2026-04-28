import pytesseract
from PIL import Image
from pdf2image import convert_from_path

import os
from dotenv import load_dotenv

load_dotenv()

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
POPPLER_PATH = os.getenv("POPPLER_PATH", r"C:\Program Files\poppler\Library\bin")

def ocr_image(path):
    img = Image.open(path)
    text = pytesseract.image_to_string(img)
    return text


def ocr_pdf(path):
    pages = convert_from_path(path, dpi=300, poppler_path=POPPLER_PATH)
    text_output = ""
    for p in pages:
        text_output += pytesseract.image_to_string(p) + "\n"
    return text_output


def extract(file_path):
    if file_path.lower().endswith(".pdf"):
        text = ocr_pdf(file_path)
    else:
        text = ocr_image(file_path)

    return text