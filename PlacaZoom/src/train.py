import os
from ultralytics import YOLO

# Load a model
model = YOLO(os.path.join("dataset", "yolov9s.pt"))  # load a pretrained model (recommended for training)
# Train the model
results = model.train(data=os.path.join("assets", "yolo", "dataset", "coco8.yaml"), epochs=100, imgsz=640) 