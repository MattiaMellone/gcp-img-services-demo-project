# Schede tecniche dei servizi

## preprocess_service

- **Endpoint**: `POST /preprocess`
- **Input**: file immagine (`multipart/form-data`)
- **Elaborazione**:
  1. Converte l'immagine in scala di grigi
  2. Effettua il resize a 224×224
  3. Applica Canny edge detection
  4. Salva il risultato come PNG sul bucket indicato dalla variabile `BUCKET`
- **Output**: `{"gcs_path": "gs://<bucket>/<file>.png"}`
- **Variabili d'ambiente**: `BUCKET` nome del bucket Cloud Storage

## classify_service

- **Endpoint**: `POST /classify`
- **Input**: JSON `{ "gcs_path": "gs://..." }`
- **Elaborazione**:
  1. Scarica l'immagine dal percorso indicato
  2. Classifica l'immagine con MobileNetV2 preaddestrata su ImageNet
- **Output**: `{"label": "<classe>", "confidence": <probabilità>}`
- **Variabili d'ambiente**: nessuna, utilizza il percorso GCS fornito in input
