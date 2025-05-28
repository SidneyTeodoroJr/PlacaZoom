import os
import re
from base64 import b64encode
from ultralytics import YOLO
import easyocr

from cv2 import (
    cvtColor, COLOR_BGR2RGB, COLOR_BGR2GRAY,
    threshold, THRESH_BINARY, THRESH_OTSU,
    putText, FONT_HERSHEY_SIMPLEX, line, imencode
)

MODEL_PATH = os.path.join("assets", "yolo", "dataset", "license_plate_detector.pt")

model = YOLO(MODEL_PATH)
reader = easyocr.Reader(['en', 'pt'])

def draw_corner_boxes(img, box, color=(255, 255, 255), thickness=2, length=20):
    x1, y1, x2, y2 = box
    line(img, (x1, y1), (x1 + length, y1), color, thickness)
    line(img, (x1, y1), (x1, y1 + length), color, thickness)
    line(img, (x2, y1), (x2 - length, y1), color, thickness)
    line(img, (x2, y1), (x2, y1 + length), color, thickness)
    line(img, (x1, y2), (x1 + length, y2), color, thickness)
    line(img, (x1, y2), (x1, y2 - length), color, thickness)
    line(img, (x2, y2), (x2 - length, y2), color, thickness)
    line(img, (x2, y2), (x2, y2 - length), color, thickness)

def preprocess_plate_image(cropped_plate):
    gray = cvtColor(cropped_plate, COLOR_BGR2GRAY)
    _, thresh = threshold(gray, 0, 255, THRESH_BINARY + THRESH_OTSU)
    return thresh

def extract_plate_text(ocr_results):
    texts = [res[1].upper() for res in ocr_results]
    ignore_words = {"BRASIL", "BR"}
    filtered_texts = [t for t in texts if t not in ignore_words]
    combined_text = "".join(filtered_texts)
    pattern = r'[A-Z]{3}\d{1}[A-Z0-9]{1}\d{2}|\b[A-Z]{3}\d{4}\b'
    match = re.search(pattern, combined_text)
    if match:
        return match.group(0)
    elif filtered_texts:
        return filtered_texts[0]
    else:
        return ""

def process_image(img):
    img_rgb = cvtColor(img, COLOR_BGR2RGB)
    results = model(img_rgb)
    annotated_img = img.copy()
    cropped_plate_base64 = None
    plate_text = ""

    for result in results:
        if result.boxes is not None and result.boxes.xyxy is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            for box in boxes:
                x1, y1, x2, y2 = box.astype(int)
                draw_corner_boxes(annotated_img, (x1, y1, x2, y2), color=(255, 255, 255), thickness=1, length=10)
                cropped_plate = img[y1:y2, x1:x2]
                preprocessed_plate = preprocess_plate_image(cropped_plate)
                result_ocr = reader.readtext(preprocessed_plate)
                if result_ocr:
                    plate_text = extract_plate_text(result_ocr)
                _, cropped_buffer = imencode('.jpg', cropped_plate)
                cropped_plate_base64 = b64encode(cropped_buffer).decode('utf-8')
                putText(
                    annotated_img,
                    plate_text if plate_text else "Plate Detected",
                    (x1, y2 + 20),
                    FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    1
                )

    _, buffer = imencode('.jpg', annotated_img)
    img_base64 = b64encode(buffer).decode('utf-8')
    return img_base64, cropped_plate_base64, plate_text