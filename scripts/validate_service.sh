#!/bin/bash
set -euo pipefail

HEALTH_URL="http://127.0.0.1:8000/health"
RETRIES=6
SLEEP=5

echo "[validate] Checking service health at ${HEALTH_URL}..."

for i in $(seq 1 $RETRIES); do
  if curl -sSf "$HEALTH_URL" -o /tmp/health.json; then
    echo "[validate] HTTP check succeeded."
    break
  else
    echo "[validate] attempt $i/$RETRIES failed; sleeping ${SLEEP}s..."
    sleep $SLEEP
  fi
  if [ "$i" -eq "$RETRIES" ]; then
    echo "[validate] service failed to respond; exiting."
    cat /tmp/health.json || true
    exit 2
  fi
done

# Optional jq usage; but avoid requiring jq. Use grep to check build version presence:
if grep -q '"status"' /tmp/health.json && grep -q '"version"' /tmp/health.json; then
  VERSION=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' /tmp/health.json | head -1 | sed -E 's/.*: *"([^"]*)"/\1/')
  echo "[validate] Health JSON returned version=${VERSION}"
  if [ -z "$VERSION" ] || [ "$VERSION" = "null" ]; then
    echo "[validate] No BUILD_VERSION present in /health output - failing validation."
    cat /tmp/health.json
    exit 3
  fi
else
  echo "[validate] Health JSON missing required fields:"
  cat /tmp/health.json
  exit 4
fi

echo "[validate] Service validation OK."