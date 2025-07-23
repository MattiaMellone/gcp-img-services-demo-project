from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import storage
import cv2
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
import tensorflow as tf

app = FastAPI()

storage_client = storage.Client()
model = MobileNetV2(weights="imagenet")

class ImagePath(BaseModel):
    gcs_path: str

@app.post("/classify")
async def classify(item: ImagePath):
    gcs_path = item.gcs_path
    if not gcs_path.startswith("gs://"):
        return {"error": "Invalid gcs_path"}
    path = gcs_path[5:]
    bucket_name, blob_name = path.split("/", 1)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    img_array = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224)).astype(np.float32)
    img = preprocess_input(img)
    img = np.expand_dims(img, 0)
    preds = model.predict(img)
    label, desc, conf = decode_predictions(preds, top=1)[0][0]
    return {"label": desc, "confidence": float(conf)}
