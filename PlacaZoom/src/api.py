import easyocr
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from base64 import b64encode
from os.path import join
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carrega modelo YOLO para detectar placa
from ultralytics import YOLO
model = YOLO(join("assets", "yolo", "dataset", "license_plate_detector.pt"))

# Carrega easyocr (em inglês e português)
reader = easyocr.Reader(['en', 'pt'])

def draw_corner_boxes(img, box, color=(255, 255, 255), thickness=2, length=20):
    x1, y1, x2, y2 = box
    # Desenho dos cantos (igual seu código)

    # Top-left corner
    cv2.line(img, (x1, y1), (x1 + length, y1), color, thickness)
    cv2.line(img, (x1, y1), (x1, y1 + length), color, thickness)

    # Top-right corner
    cv2.line(img, (x2, y1), (x2 - length, y1), color, thickness)
    cv2.line(img, (x2, y1), (x2, y1 + length), color, thickness)

    # Bottom-left corner
    cv2.line(img, (x1, y2), (x1 + length, y2), color, thickness)
    cv2.line(img, (x1, y2), (x1, y2 - length), color, thickness)

    # Bottom-right corner
    cv2.line(img, (x2, y2), (x2 - length, y2), color, thickness)
    cv2.line(img, (x2, y2), (x2, y2 - length), color, thickness)

def preprocess_plate_image(cropped_plate):
    # Converte para escala de cinza
    gray = cv2.cvtColor(cropped_plate, cv2.COLOR_BGR2GRAY)
    # Binariza a imagem usando Otsu para melhorar o contraste
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Você pode tentar também dilatação/erosão se necessário
    return thresh

def extract_plate_text(ocr_results):
    texts = [res[1].upper() for res in ocr_results]
    ignore_words = {"BRASIL", "BR"}

    filtered_texts = [t for t in texts if t not in ignore_words]

    combined_text = "".join(filtered_texts)

    # Regex para placas brasileiras - Mercosul e padrão antigo
    pattern = r'[A-Z]{3}\d{1}[A-Z0-9]{1}\d{2}|\b[A-Z]{3}\d{4}\b'

    match = re.search(pattern, combined_text)
    if match:
        return match.group(0)
    elif filtered_texts:
        return filtered_texts[0]  # fallback para primeiro texto filtrado
    else:
        return ""

def process_image(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = model(img_rgb)

    annotated_img = img.copy()
    cropped_plate_base64 = None
    plate_text = ""

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()

        for box in boxes:
            x1, y1, x2, y2 = box.astype(int)
            draw_corner_boxes(annotated_img, (x1, y1, x2, y2), color=(255, 255, 255), thickness=1, length=10)

            cropped_plate = img[y1:y2, x1:x2]

            # Pré-processa a imagem da placa para melhorar OCR
            preprocessed_plate = preprocess_plate_image(cropped_plate)

            # Usa easyocr para ler texto na placa pré-processada
            result_ocr = reader.readtext(preprocessed_plate)

            if result_ocr:
                plate_text = extract_plate_text(result_ocr)

            # Codifica recorte da placa em base64
            _, cropped_buffer = cv2.imencode('.jpg', cropped_plate)
            cropped_plate_base64 = b64encode(cropped_buffer).decode('utf-8')

            cv2.putText(
                annotated_img,
                plate_text if plate_text else "Plate Detected",
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                1
            )

    _, buffer = cv2.imencode('.jpg', annotated_img)
    img_base64 = b64encode(buffer).decode('utf-8')

    return img_base64, cropped_plate_base64, plate_text

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    img_base64, cropped_plate_base64, plate_text = process_image(img)

    return JSONResponse(content={
        "image_base64": img_base64,
        "plate_crop_base64": cropped_plate_base64,
        "plate_text": plate_text
    })