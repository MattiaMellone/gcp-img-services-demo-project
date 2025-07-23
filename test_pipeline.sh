#!/usr/bin/env bash
# run_pipeline.sh ───────────────────────────────────────────────
# Elabora tutte le immagini in ./test_imgs con la pipeline GCP

set -euo pipefail

# ────────────────────────────
# ID‑token per servizi privati
# ────────────────────────────
TOKEN=$(gcloud auth print-identity-token)

# ────────────────────────────
# Endpoint Cloud Run (includono già /preprocess e /classify)
# ────────────────────────────
PRE="https://preprocess-service-763687517262.europe-west1.run.app/preprocess"
CLS="https://classify-service-763687517262.europe-west1.run.app/classify"

# ────────────────────────────
# Directory immagini
# ────────────────────────────
IMG_DIR="$(dirname "$0")/test_imgs"

# accetta .jpg .jpeg .png
shopt -s nullglob
IMGS=("$IMG_DIR"/*.{jpg,jpeg,png})

[[ ${#IMGS[@]} -eq 0 ]] && {
  echo "❌  Nessuna immagine trovata in $IMG_DIR"
  exit 1
}

# ────────────────────────────
# Loop sulle immagini
# ────────────────────────────
for IMG in "${IMGS[@]}"; do
  echo "▶︎ Processing $(basename "$IMG")"

  # 1. PRE‑PROCESS
  PREP_JSON=$(curl -sSf \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@${IMG}" \
    "$PRE")

  echo "  • preprocess → $PREP_JSON"

  # 2. CLASSIFY
  CLS_JSON=$(curl -sSf \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$PREP_JSON" \
    "$CLS")

  echo "  • classify   → $CLS_JSON"
  echo
done
