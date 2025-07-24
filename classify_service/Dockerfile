FROM python:3.11-slim

WORKDIR /app

# --- librerie native richieste da OpenCV ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*
# --------------------------------------------

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre‑scarica i pesi di MobileNetV2 per ridurre il cold‑start
RUN python - <<'PY'
import tensorflow as tf
from tensorflow.keras.applications import mobilenet_v2
mobilenet_v2.MobileNetV2(weights="imagenet")
PY

COPY main.py .

ENV PORT=8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
