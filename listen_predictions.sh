#!/usr/bin/env bash
# listen_predictions.sh ──────────────────────────────────────────
# Rimane in ascolto sulla pull‑subscription $SUB_ID e stampa
# la previsione prodotta da classify_service.

set -euo pipefail

SUB_ID="${SUB_ID:-img-classified-test}"
PROJECT_ID="$(gcloud config get-value project)"

echo "╭───────────────────────────────────────"
echo "│  Listening on subscription: $SUB_ID"
echo "╰───────────────────────────────────────"
echo

while true; do
  # Estrae al massimo 10 messaggi, li ack-a e stampa il payload JSON
  gcloud pubsub subscriptions pull "$SUB_ID" \
        --project="$PROJECT_ID" \
        --limit=10 --auto-ack --format='json' |
  jq -r '.[].message.data' |    # prende il campo data base64…
  base64 --decode |             # …lo decodifica…
  jq . || true                  # …e lo stampa come JSON (se c’è)
  sleep 2                       # piccola pausa fra i poll
done
