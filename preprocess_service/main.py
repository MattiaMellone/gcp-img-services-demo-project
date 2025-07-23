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
    img   = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


    img   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img   = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
    ret, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ret:
        return {"error": "Encoding failed"}

    filename = f"{uuid.uuid4()}.jpg"
    bucket   = storage_client.bucket(bucket_name)
    bucket.blob(filename).upload_from_string(buf.tobytes(),
                                             content_type="image/jpeg")

    return {"gcs_path": f"gs://{bucket_name}/{filename}"}
