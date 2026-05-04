FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface

WORKDIR /app

# System deps for librosa (libsndfile, ffmpeg) and OpenCV/DeepFace (libGL, libglib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend code (DSM5.pdf + RAG cache, if pre-built locally, ride along)
COPY backend/ ./backend/

# Pre-warm the sentence-transformer + RAG index so first request is instant.
# Failures here (e.g. no network at build time) fall back to first-run rebuild.
RUN cd backend && python -c "import rag" || echo "[warn] RAG pre-warm skipped; will build on first request"

# Drop privileges
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 8000

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
