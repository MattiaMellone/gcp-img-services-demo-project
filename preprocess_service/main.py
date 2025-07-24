"""Image preprocessing micro‑service.

Receives an image upload, converts it to RGB 224×224 JPEG, stores it on
Google Cloud Storage and publishes a message on Pub/Sub so that downstream
consumers (e.g. *classify_service*) can continue the pipeline.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
import cv2
import numpy as np
import os
import uuid
import json
import logging
from google.cloud import storage, pubsub_v1
from google.api_core.exceptions import GoogleAPICallError
import google.auth


app = FastAPI()
logger = logging.getLogger("uvicorn.error")  # logger usato da Uvicorn

# --------------------------------------------------------------------------- #
#  Runtime configuration                                                      #
# --------------------------------------------------------------------------- #
BUCKET_NAME = os.getenv("BUCKET")  # target GCS bucket
if not BUCKET_NAME:
    raise RuntimeError("Environment variable BUCKET is not set")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    _, PROJECT_ID = google.auth.default()


PUB_TOPIC = os.getenv("PREP_TOPIC", "img-preprocessed")

storage_client = storage.Client()
publisher_client = pubsub_v1.PublisherClient()
TOPIC_PATH = publisher_client.topic_path(PROJECT_ID, PUB_TOPIC)


# --------------------------------------------------------------------------- #
#  Endpoint                                                                   #
# --------------------------------------------------------------------------- #
@app.post("/preprocess")
async def preprocess(file: UploadFile = File(...)) -> dict[str, str]:
    """Process an uploaded image and publish its GCS path.

    Args:
        file: Multipart image file sent by the client.

    Returns:
        {"gcs_path": "...", "message_id": "..."}
    """
    data = await file.read()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)

    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise HTTPException(status_code=500, detail="Encoding failed")

    filename = f"{uuid.uuid4()}.jpg"
    bucket = storage_client.bucket(BUCKET_NAME)
    bucket.blob(filename).upload_from_string(
        buf.tobytes(), content_type="image/jpeg"
    )

    gcs_path = f"gs://{BUCKET_NAME}/{filename}"

    # Publish a JSON payload to Pub/Sub for downstream processing.
    payload = json.dumps({"gcs_path": gcs_path}).encode()

    try:
        future = publisher_client.publish(
            TOPIC_PATH, payload, origin="preprocess-service"
        )
        message_id = future.result(timeout=10)  # blocca finché Pub/Sub conferma
        logger.info("Published message %s to topic %s", message_id, TOPIC_PATH)
    except GoogleAPICallError as err:
        logger.error("Publish failed: %s", err)
        raise HTTPException(status_code=502, detail="Publish to Pub/Sub failed") from err
    except Exception as err:  # timeout o altri errori
        logger.error("Unexpected publish error: %s", err)
        raise HTTPException(status_code=500, detail="Unexpected publish error") from err

    return {"gcs_path": gcs_path, "message_id": message_id}
