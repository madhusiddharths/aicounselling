#!/usr/bin/env sh
set -e

# On platforms where secrets are injected as environment variables rather than
# files (e.g. Hugging Face Spaces), materialize the Google service-account JSON
# to disk so the google-cloud libraries (GCS download + Text-to-Speech) can
# authenticate. This is a no-op locally when GCP_SA_JSON is unset — the existing
# GOOGLE_APPLICATION_CREDENTIALS / TTS_CREDENTIALS paths from .env are used as-is.
if [ -n "$GCP_SA_JSON" ]; then
  printf '%s' "$GCP_SA_JSON" > /tmp/gcp-sa.json
  export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-sa.json
  : "${TTS_CREDENTIALS:=/tmp/gcp-sa.json}"
  export TTS_CREDENTIALS
fi

# HF Spaces sets the listening port via app_port in README; honor $PORT if present.
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
