import os
import tempfile
import subprocess
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage
import speech_recognition as sr
from pydub import AudioSegment, effects
from pydub.effects import high_pass_filter, low_pass_filter, compress_dynamic_range

# ---------- config ----------
CHUNK_SEC = 50
LANG = "en-US"
MIN_SIZE_BYTES = 8192   # skip tiny/partial chunks
# ---------------------------

load_dotenv(override=True)

GCS_BUCKET  = os.getenv("GCS_BUCKET")
USERS_BASE_PREFIX = os.getenv("USERS_BASE_PREFIX", "users/")
RECORD_SUBPATH    = os.getenv("RECORD_SUBPATH", "audio/webm/")

if not GCS_BUCKET:
    raise SystemExit("Set GCS_BUCKET in .env")

def _gcs():
    return storage.Client()

def list_users(bucket_name: str, base_prefix: str):
    client = _gcs()
    bucket = client.bucket(bucket_name)
    blobs = client.list_blobs(bucket, prefix=base_prefix.rstrip("/") + "/", delimiter="/")
    
    # Trigger listing to populate prefixes
    for _ in blobs:
        pass
        
    out = []
    for prefix in blobs.prefixes:
        # prefix format: users/user_xxx/
        user_id = prefix.rstrip("/").split("/")[-1]
        out.append(user_id)
    return out

def list_latest_objects(bucket_name: str, users_base: str, record_subpath: str, limit=50, user_id=None):
    """Return newest objects. If user_id is provided, only for that user. Else across all."""
    client = _gcs()
    bucket = client.bucket(bucket_name)
    items = []
    
    if user_id:
        users = [user_id]
    else:
        users = list_users(bucket_name, users_base)

    for user in users:
        prefix = f"{users_base.rstrip('/')}/{user}/{record_subpath.strip('/')}/"
        blobs = client.list_blobs(bucket, prefix=prefix)
        for blob in blobs:
            key, size, ts = blob.name, blob.size, blob.updated
            if key.endswith("/") or size < MIN_SIZE_BYTES:  # skip folders & tiny chunks
                continue
            items.append({"Key": key, "Size": size, "LastModified": ts})
    items.sort(key=lambda x: x["LastModified"], reverse=True)
    return items[:limit]

def download_to_temp(bucket_name: str, key: str) -> str:
    client = _gcs()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(key)
    suffix = Path(key).suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp.name; tmp.close()
    blob.download_to_filename(tmp_path)
    return tmp_path

# ---- robust decode helpers ----
def ffmpeg_decode_to_wav_bytes(in_path: str) -> bytes:
    """Try a tolerant ffmpeg transcode to mono 16k WAV -> bytes."""
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-err_detect", "ignore_err",
        "-i", in_path,
        "-ac", "1", "-ar", "16000",
        "-f", "wav", "-max_muxing_queue_size", "1024", "pipe:1"
    ]
    # Do not crash if ffmpeg returns non-zero, as long as it outputs SOME wav bytes
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True)
        return proc.stdout
    except subprocess.CalledProcessError as e:
        if len(e.stdout) > 0:
            return e.stdout  # Salvaged bytes
        raise e

def load_audio_robust(in_path: str) -> AudioSegment:
    """
    Try pydub first; if it fails, fall back to ffmpeg CLI to WAV bytes.
    Raise on hard failure so caller can try an older object.
    """
    try:
        # Pydub often fails on incomplete WebM chunks
        return AudioSegment.from_file(in_path)
    except Exception:
        # Fallback: tolerant decode to WAV bytes
        try:
            pcm = ffmpeg_decode_to_wav_bytes(in_path)
            return AudioSegment.from_file(BytesIO(pcm), format="wav")
        except Exception as e:
            print(f"Both pydub and ffmpeg fallback failed: {e}")
            raise

# ---- preprocessing + ASR ----
def preprocess(seg: AudioSegment) -> AudioSegment:
    seg = seg.set_channels(1).set_frame_rate(16000)
    seg = high_pass_filter(seg, cutoff=100)
    seg = low_pass_filter(seg, cutoff=8000)
    seg = effects.normalize(seg)
    seg = compress_dynamic_range(seg, threshold=-20.0, ratio=4.0, attack=5, release=50)
    return seg

def chunk(seg: AudioSegment, seconds=CHUNK_SEC):
    step = int(seconds * 1000)
    return [seg[i:i+step] for i in range(0, len(seg), step)]

# Global cache of processed keys to prevent replaying the same question across calls
PROCESSED_AUDIO_KEYS = set()

def collect_last_k_decodable(bucket: str, candidates: list[dict], k: int = 3):
    """Try candidates newest->oldest, decode those that work (up to k), return a single concatenated AudioSegment."""
    got = []
    for obj in candidates:
        key = obj["Key"]
        
        # Skip chunks we already processed
        if key in PROCESSED_AUDIO_KEYS:
            continue
            
        try:
            local = download_to_temp(bucket, key)
            raw = load_audio_robust(local)
            got.append(raw)
            print(f"collected: {key}")
            
            # Mark as processed
            PROCESSED_AUDIO_KEYS.add(key)
            
            if len(got) >= k:
                break
        except Exception as e:
            print(f"skip {key}: {e}")
        finally:
            try: os.remove(local)
            except: pass
            
    if not got:
        raise RuntimeError("No new decodable audio found.")
        
    # concatenate and preprocess once
    merged = got[0]
    for seg in got[1:]:
        merged += seg
    return preprocess(merged)

def _recognize_segment(audio_chunk, idx: int, total: int) -> str:
    r = sr.Recognizer()
    try:
        res = r.recognize_google(audio_chunk, language=LANG, show_all=True)
        if isinstance(res, dict) and res.get("alternative"):
            best = max(res["alternative"], key=lambda a: a.get("confidence", 0))
            text = (best.get("transcript") or "").strip()
        else:
            text = r.recognize_google(audio_chunk, language=LANG).strip()
        print(f"[{idx}/{total}] ✓")
        return text
    except sr.UnknownValueError:
        print(f"[{idx}/{total}] (no speech recognized)")
        return ""
    except sr.RequestError as e:
        print(f"[{idx}/{total}] API error: {e}")
        return ""


def _transcribe_segment(seg: AudioSegment) -> str:
    parts = chunk(seg)
    r = sr.Recognizer()
    out = []
    with tempfile.TemporaryDirectory() as td:
        for i, p in enumerate(parts, 1):
            wav = os.path.join(td, f"part_{i}.wav")
            p.export(wav, format="wav")
            with sr.AudioFile(wav) as src:
                r.adjust_for_ambient_noise(src, duration=0.3)
                audio_chunk = r.record(src)
            text = _recognize_segment(audio_chunk, i, len(parts))
            if text:
                out.append(text)
    return " ".join(out).strip()


def transcribe_latest_concat(bucket: str, k: int = 3, pool=30, user_id=None) -> str:
    candidates = list_latest_objects(bucket, USERS_BASE_PREFIX, RECORD_SUBPATH, limit=pool, user_id=user_id)
    merged = collect_last_k_decodable(bucket, candidates, k=k)
    return _transcribe_segment(merged)


def transcribe_local(local_path: str) -> str:
    """Transcribe a local audio/video file directly."""
    try:
        raw = load_audio_robust(local_path)
        return _transcribe_segment(preprocess(raw))
    except Exception as e:
        print(f"transcribe_local error: {e}")
        return ""

