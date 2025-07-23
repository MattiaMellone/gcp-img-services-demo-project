from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
import os
import uuid
from google.cloud import storage

app = FastAPI()

bucket_name = os.getenv("BUCKET")
storage_client = storage.Client()

@app.post("/preprocess")
async def preprocess(file: UploadFile = File(...)):
    data = await file.read()
    img_array = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (224, 224))
    edges = cv2.Canny(resized, 100, 200)
    _, png = cv2.imencode('.png', edges)
    filename = f"{uuid.uuid4()}.png"
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(png.tobytes(), content_type='image/png')
    gcs_path = f"gs://{bucket_name}/{filename}"
    return {"gcs_path": gcs_path}
