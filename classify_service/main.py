"""Image classification micro‑service based on MobileNetV2.

Provides two endpoints:

* POST */classify* — synchronous classification given a ``gs://`` URI.
* POST */pubsub*  — receives Pub/Sub push messages (JSON envelope) and
  performs the same classification automatically.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from google.cloud import storage, pubsub_v1
import cv2
import numpy as np
import base64
import json
from tensorflow.keras.applications.mobilenet_v2 import (
    MobileNetV2,
    preprocess_input,
    decode_predictions,
)
import os
import google.auth


app = FastAPI()


PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    _, PROJECT_ID = google.auth.default()

CLASS_TOPIC  = os.getenv("CLASS_TOPIC", "img-classified")
publisher    = pubsub_v1.PublisherClient()
CLASS_PATH   = publisher.topic_path(PROJECT_ID, CLASS_TOPIC)

storage_client = storage.Client()
model = MobileNetV2(weights="imagenet")  # loaded once at cold start


# --------------------------------------------------------------------------- #
#  Utility                                                                    #
# --------------------------------------------------------------------------- #
def _predict(gcs_path: str) -> dict[str, str | float]:
    """Run MobileNetV2 on the image located at *gcs_path*."""
    if not gcs_path.startswith("gs://"):
        raise HTTPException(status_code=400, detail="gcs_path must start with gs://")

    bucket_name, blob_name = gcs_path[5:].split("/", 1)
    bucket = storage_client.bucket(bucket_name)
    blob   = bucket.blob(blob_name)

    try:
        data = blob.download_as_bytes()
    except Exception as err:
        raise HTTPException(status_code=404, detail="Image not found") from err

    img_arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img_arr is None:
        raise HTTPException(status_code=400, detail="Corrupted image data")

    img = cv2.cvtColor(img_arr, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224)).astype(np.float32)
    img = preprocess_input(img)[None, ...]        # add batch dim

    preds = model.predict(img, verbose=0)
    _, label, conf = decode_predictions(preds, top=1)[0][0]
    return {"label": label, "confidence": float(conf)}


# --------------------------------------------------------------------------- #
#  API payload schemas                                                        #
# --------------------------------------------------------------------------- #
class ImagePath(BaseModel):
    """Body for /classify."""

    gcs_path: str


# --------------------------------------------------------------------------- #
#  Endpoints                                                                  #
# --------------------------------------------------------------------------- #
@app.post("/classify")
async def classify(item: ImagePath) -> dict[str, str | float]:
    """Synchronous prediction endpoint."""
    return _predict(item.gcs_path)


@app.post("/pubsub")
async def pubsub_push(request: Request) -> dict[str, str | float]:
    """Endpoint for Pub/Sub push (JSON envelope, OIDC‑authenticated).

    The expected envelope shape is:

        {
          "message": {
              "data": "<base64‑json‑payload>",
              "attributes": { ... },
              ...
          },
          "subscription": "projects/…"
        }

    The inner payload must be ``{"gcs_path": "gs://…/image.jpg"}``.
    """
    envelope = await request.json()
    message  = envelope.get("message", {})
    data_b64 = message.get("data", "")

    try:
        payload   = json.loads(base64.b64decode(data_b64).decode())
        gcs_path  = payload["gcs_path"]
    except (ValueError, KeyError):
        raise HTTPException(status_code=400, detail="Bad Pub/Sub message")

    result = _predict(gcs_path)
    publisher.publish(
        CLASS_PATH,
        json.dumps({"gcs_path": gcs_path, **result}).encode(),
        origin="classify-service"
    )
    return {"status": "ok", **result}
