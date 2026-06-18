FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface

WORKDIR /app

# System deps for librosa/pydub audio decoding (libsndfile, ffmpeg).
# Face emotion now runs in the browser, so OpenCV/DeepFace libs are no longer needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code (DSM5.pdf + RAG cache, if pre-built locally, ride along)
COPY backend/ ./backend/

# Bake the ML models into the image layer so cold starts don't re-download them:
# the RAG sentence-transformer + index, and the Wav2Vec2 voice-tone model (~360 MB).
# Failures here (e.g. no network at build time) fall back to first-run download.
RUN cd backend && python -c "import rag" \
    && python -c "from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor; m='r-f/wav2vec-english-speech-emotion-recognition'; Wav2Vec2FeatureExtractor.from_pretrained(m); Wav2Vec2ForSequenceClassification.from_pretrained(m)" \
    || echo "[warn] model pre-warm skipped; will download on first request"

# Drop privileges
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 8000

WORKDIR /app/backend
# entrypoint.sh materializes the GCP service-account JSON from $GCP_SA_JSON (HF
# Spaces secrets) before launching uvicorn; falls back to plain uvicorn locally.
CMD ["sh", "entrypoint.sh"]
