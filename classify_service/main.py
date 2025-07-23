"""Image classification microservice powered by MobileNetV2.

The service retrieves a preprocessed image from Google Cloud Storage and
produces a prediction using a pre-trained MobileNetV2 model.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from google.cloud import storage
import cv2
import numpy as np
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
    decode_predictions,
)
import tensorflow as tf

app = FastAPI()

storage_client = storage.Client()
model = MobileNetV2(weights="imagenet")

class ImagePath(BaseModel):
    """Path of the image to classify."""

    gcs_path: str

@app.post("/classify")
async def classify(item: ImagePath):
    """Fetch an image from Cloud Storage and predict its class.

    Args:
        item: Object containing the ``gs://`` path of the preprocessed image.

    Returns:
        JSON document with ``label`` and ``confidence`` keys. If the path is
        invalid an ``error`` field is returned instead.
    """

    gcs_path = item.gcs_path
    if not gcs_path.startswith("gs://"):
        return {"error": "Invalid gcs_path"}
    path = gcs_path[5:]  # strip "gs://" prefix
    bucket_name, blob_name = path.split("/", 1)  # separate bucket and object
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    img_array = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224)).astype(np.float32)
    img = preprocess_input(img)
    img = np.expand_dims(img, 0)
    preds = model.predict(img)  # single forward pass
    label, desc, conf = decode_predictions(preds, top=1)[0][0]
    return {"label": desc, "confidence": float(conf)}
