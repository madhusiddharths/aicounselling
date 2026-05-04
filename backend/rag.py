"""DSM-5 retrieval over a local PDF.

Builds (or loads from cache) a sentence-transformer embedding index over the DSM-5,
then retrieves chunks for a query. Cache invalidates automatically when the
PDF, chunking config, or embedding model changes.
"""

import json
import os
from dataclasses import dataclass

import faiss
import numpy as np
import PyPDF2
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(__file__)
PDF_PATH = os.path.join(BASE_DIR, "DSM5.pdf")

MODEL_NAME = "all-mpnet-base-v2"
CHUNK_SIZE = 400          # words per chunk
CHUNK_OVERLAP = 80        # words shared between adjacent chunks
TOP_K = 5
MIN_SCORE = 0.25          # cosine similarity floor; lower = irrelevant noise

CHUNKS_PATH = os.path.join(BASE_DIR, "dsm5_chunks.json")
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "dsm5_embeddings.npy")
MANIFEST_PATH = os.path.join(BASE_DIR, "dsm5_manifest.json")
LEGACY_EMBEDDINGS = os.path.join(BASE_DIR, "document_embeddings.npy")


@dataclass
class _Index:
    chunks: list
    index: faiss.IndexFlatIP
    model: SentenceTransformer


def _extract_pdf_text(path: str) -> str:
    text = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n".join(text)


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, chunk_size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        piece = words[i : i + chunk_size]
        if len(piece) < max(40, overlap):
            break
        chunks.append(" ".join(piece))
    return chunks


def _manifest(pdf_path: str) -> dict:
    return {
        "model": MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "overlap": CHUNK_OVERLAP,
        "pdf_size": os.path.getsize(pdf_path),
    }


def _cache_valid(pdf_path: str) -> bool:
    if not (os.path.exists(EMBEDDINGS_PATH) and os.path.exists(CHUNKS_PATH) and os.path.exists(MANIFEST_PATH)):
        return False
    try:
        with open(MANIFEST_PATH) as f:
            saved = json.load(f)
    except Exception:
        return False
    return saved == _manifest(pdf_path)


def _build(pdf_path: str, model: SentenceTransformer) -> tuple[list[str], np.ndarray]:
    print("[rag] Building DSM-5 index (one-time, ~1-3 min)...")
    text = _extract_pdf_text(pdf_path)
    chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False, batch_size=32)
    embeddings = embeddings.astype(np.float32)
    faiss.normalize_L2(embeddings)

    np.save(EMBEDDINGS_PATH, embeddings)
    with open(CHUNKS_PATH, "w") as f:
        json.dump(chunks, f)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(_manifest(pdf_path), f)
    print(f"[rag] Built {len(chunks)} chunks, embedding dim {embeddings.shape[1]}")
    return chunks, embeddings


def _load(model: SentenceTransformer) -> tuple[list[str], np.ndarray]:
    with open(CHUNKS_PATH) as f:
        chunks = json.load(f)
    embeddings = np.load(EMBEDDINGS_PATH).astype(np.float32)
    if embeddings.shape[0] != len(chunks):
        raise RuntimeError(
            f"[rag] cache mismatch: {embeddings.shape[0]} embeddings vs {len(chunks)} chunks"
        )
    faiss.normalize_L2(embeddings)
    print(f"[rag] Loaded cached index: {len(chunks)} chunks, dim {embeddings.shape[1]}")
    return chunks, embeddings


def _init() -> _Index:
    model = SentenceTransformer(MODEL_NAME)
    if _cache_valid(PDF_PATH):
        chunks, embeddings = _load(model)
    else:
        # Best-effort cleanup of legacy artifact from old chunking config
        if os.path.exists(LEGACY_EMBEDDINGS):
            try:
                os.remove(LEGACY_EMBEDDINGS)
            except OSError:
                pass
        chunks, embeddings = _build(PDF_PATH, model)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return _Index(chunks=chunks, index=index, model=model)


_INDEX: _Index = _init()


def retrieve_chunks(query: str, top_k: int = TOP_K, min_score: float = MIN_SCORE) -> list[str]:
    """Return chunks above min_score, in similarity order."""
    if not query or not query.strip():
        return []

    q_emb = _INDEX.model.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(q_emb)
    scores, ids = _INDEX.index.search(q_emb, top_k)

    hits = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(_INDEX.chunks):
            continue
        if score < min_score:
            continue
        hits.append((float(score), _INDEX.chunks[idx]))

    if hits:
        top_score = hits[0][0]
        print(f"[rag] q={query[:60]!r} top={top_score:.3f} hits={len(hits)}")
    else:
        print(f"[rag] q={query[:60]!r} no hits above {min_score}")

    return [chunk for _, chunk in hits]
