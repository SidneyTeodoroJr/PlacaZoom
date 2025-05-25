import os
import cv2
import time
import psutil
import base64
from io import BytesIO
from ultralytics import YOLO
from collections import Counter
import threading

def yolo(update_image_callback, stop_flag):
    def draw_rounded_rect(img, top_left, bottom_right, color, radius=20, thickness=-1):
        x1, y1 = top_left
        x2, y2 = bottom_right
        img = cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
        img = cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
        img = cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
        img = cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
        img = cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
        img = cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)
        return img

    def generate_dynamic_color(cls_idx):
        red = (cls_idx * 30) % 256
        green = (cls_idx * 60) % 256
        blue = (cls_idx * 90) % 256
        return (red, green, blue)

    model = YOLO(os.path.join("dataset", "yolov9s.pt"))
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro ao abrir a câmera!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    while not stop_flag["stop"]:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = model(img_rgb)
        frame_display = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            cls = int(box.cls[0].cpu().item())
            label = results[0].names[cls]
            color = generate_dynamic_color(cls)
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame_display, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        _, buffer = cv2.imencode('.jpg', frame_display)
        img_bytes = buffer.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        update_image_callback(img_base64)
    
    cap.release()
