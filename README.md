# gcp-img-services-demo-project

This repository contains a demo composed of two small FastAPI microservices that can be deployed to Google Cloud Run. They work together to preprocess an image and classify it using MobileNetV2.

## Services

- **preprocess_service** – receives an image, converts it to grayscale, resizes it to 224×224, runs Canny edge detection and saves the result as PNG into a Google Cloud Storage bucket specified by the `BUCKET` environment variable.
- **classify_service** – receives the `gcs_path` of a processed image, downloads it from Cloud Storage and performs image classification with MobileNetV2 (`weights="imagenet"`).

## Requirements

- Docker
- Google Cloud account with Artifact Registry and Cloud Run enabled
- Python 3.11 for local execution

## Quick start

```bash
# Preprocess service
cd preprocess_service
uvicorn main:app --reload

# In a separate terminal classify service
cd classify_service
uvicorn main:app --reload
```

Images are stored in the bucket defined by `BUCKET`. When deployed to Cloud Run the images are pushed to Artifact Registry and the services are automatically deployed.

## Architecture

```
+--------+      POST /preprocess        +------------------+
| Client | ---------------------------> | preprocess_service|
+--------+                               +------------------+
                                               |
                                               | gs://bucket/image.png
                                               v
                                        +------------------+
                                        | classify_service |
                                        +------------------+
                                               |
                                               v
                                            Prediction
```
