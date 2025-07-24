#!/usr/bin/env bash
# publish_imgs.sh ────────────────────────────────────────────────
# Invia tutte le immagini di ./test_imgs al servizio /preprocess
# Il servizio, oltre a scrivere l’immagine su GCS, pubblica un
# messaggio sul topic “img-preprocessed” – sarà poi il turn‑key del
# flusso Pub/Sub.

set -euo pipefail

# ID‑token per Cloud Run privato
TOKEN=$(gcloud auth print-identity-token)

# Endpoint Cloud Run (modifica PROJECT & REGION se necessario)
PROJECT_ID="$(gcloud config get-value project)"
REGION="europe-west1"
PRE="https://preprocess-service-visppy6x3q-ew.a.run.app/preprocess"

IMG_DIR="$(dirname "$0")/test_imgs"
shopt -s nullglob
IMGS=("$IMG_DIR"/*.{jpg,jpeg,png})

[[ ${#IMGS[@]} -eq 0 ]] && { echo "❌  Nessuna immagine in $IMG_DIR"; exit 1; }

for IMG in "${IMGS[@]}"; do
  echo "▶︎ $(basename "$IMG")"
  curl -sSf -H "Authorization: Bearer $TOKEN" -F "file=@${IMG}" "$PRE" \
    | jq .
done
