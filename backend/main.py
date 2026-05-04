import json
import logging
import os
import sys
import tempfile
import time
from collections import Counter

from dotenv import load_dotenv
load_dotenv(override=True)

import cv2
import uvicorn
import google.generativeai as genai
from deepface import DeepFace
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from process_audio_tone import SpeechProcessor, analyze_audio_ensemble
from speech_to_text import transcribe_latest_concat, transcribe_local
from mongodb_fetcher import fetch_all_from_mongo, client
from memory import get_user_summary, update_memory_lazily
from rag import retrieve_chunks
import tts


# ----- Logging -----
NOISY_PREFIXES = (
    "Batches: ", "Loading weights: ", "Wav2Vec2ForSequenceClassification",
    "MPNetModel", "Key ", "---", "classifier.", "projector.",
    "Notes:", "- UNEXPECTED", "- MISSING", "Embeddings shape",
    "Total chunks", "HTTP Request: HEAD",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


class StreamToLogger:
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            s = str(line).strip()
            if not s or s.startswith(NOISY_PREFIXES):
                continue
            self.logger.log(self.log_level, s)

    def flush(self):
        pass

    def isatty(self):
        return False


sys.stdout = StreamToLogger(logging.getLogger("STDOUT"), logging.INFO)
sys.stderr = StreamToLogger(logging.getLogger("STDERR"), logging.ERROR)

# ----- Configuration -----
MONGO_DB = os.getenv("MONGO_DB", "coach")
GCS_BUCKET = os.getenv("GCS_BUCKET")
print(f"Backend starting with GCS_BUCKET: {GCS_BUCKET}")

genai.configure(api_key=os.getenv("GOOGLE_API_KEY", ""))
gemini = genai.GenerativeModel("gemini-2.5-flash")

CRISIS_TERMS = {"suicide", "kill myself", "end my life", "self harm", "overdose", "hurt myself"}
EMPTY_TONE = {"phases": [], "distribution": {}, "total_duration": 0.0, "avg_confidence": 0.0}

SMALL_TALK_PATTERNS = {
    "hi", "hii", "hiii", "hello", "hey", "heyy", "yo", "sup", "wassup",
    "good morning", "good afternoon", "good evening", "good night", "gn", "gm",
    "how are you", "how r u", "how's it going", "hows it going", "what's up", "whats up",
    "thanks", "thank you", "ty", "thx", "ok", "okay", "k", "kk", "cool", "nice",
    "bye", "goodbye", "see ya", "see you", "later", "cya",
    "lol", "haha", "lmao",
}

STYLE_RULES = """\
Style rules — follow strictly:
- Match the user's energy and length. If they wrote one casual line, reply with one casual line.
- Do NOT bring up DSM-5 content, past conversations, their profile, or therapy frameworks unless they raise it themselves in this message.
- Do NOT lecture, list multiple suggestions, or recap what they said. No preamble.
- Substantive responses cap at 3 sentences unless the user asks for more.
- Sound like a warm friend, not a clinician.
- Never give medical advice or suggest professionals."""


def is_small_talk(text: str) -> bool:
    if not text:
        return True
    s = text.strip().lower().rstrip("!.?,")
    if len(s) <= 3:
        return True
    if s in SMALL_TALK_PATTERNS:
        return True
    if len(s.split()) <= 4 and any(s.startswith(p) for p in SMALL_TALK_PATTERNS):
        return True
    return False


def small_talk_reply(msg: str, extra_context: str = "") -> str:
    prompt = f"""You are a warm, friendly companion. The user just said: "{msg}"
{extra_context}
Reply naturally in 1-2 short sentences. Match their casual tone. Do NOT bring up therapy, mental health, past sessions, or anything analytical."""
    return (gemini.generate_content(prompt).text or "").strip()


# ----- App / shared deps -----
app = FastAPI(title="Mental Wellness & Emotion Detection API")
speech_processor = SpeechProcessor()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Mental Wellness API is running",
        "gcs_bucket": GCS_BUCKET,
        "mongo_db": MONGO_DB,
    }


def is_high_risk(text: str) -> bool:
    text = (text or "").lower()
    return any(term in text for term in CRISIS_TERMS)


def detect_emotion(frame) -> str:
    try:
        result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
        return result[0]["dominant_emotion"]
    except Exception:
        return "No face"


def fetch_questionnaire(user_id: str):
    try:
        rows = fetch_all_from_mongo("users", {"clerk_user_id": user_id})
        return rows[0] if rows else ""
    except Exception:
        return ""


def rag_context(query: str) -> str:
    if not query:
        return "No relevant content found."
    try:
        chunks = retrieve_chunks(query)
    except Exception as e:
        print(f"RAG error: {e}")
        return "No relevant content found."
    return "\n".join(chunks) if chunks else "No relevant content found."


def tts_safe(text: str) -> str:
    if not text:
        return ""
    try:
        return tts.synthesize_text(text)
    except Exception as e:
        print(f"TTS generation failed: {e}")
        return ""



@app.post("/respond")
def respond(msg, user_id):
    if is_high_risk(msg):
        reply = (
            "I'm really glad you reached out. Your safety matters. "
            "If you're in immediate danger, call your local emergency number now. "
            "You can also contact a local crisis line or reach out to someone you trust."
        )
        return {"response": {"reply": reply}}

    history_list = []
    try:
        cursor = client[MONGO_DB]["chat_history"].find({"user_id": user_id}).sort("timestamp", -1).limit(10)
        history_list = list(cursor)
        history_list.reverse()
    except Exception as e:
        print(f"Error fetching history: {e}")

    if is_small_talk(msg):
        answer = small_talk_reply(msg)
    else:
        context_text = rag_context(msg)
        questionnaire = fetch_questionnaire(user_id)

        history_text = "".join(
            f"\nUser: {h.get('user_msg')}\nAssistant: {h.get('assistant_msg')}" for h in history_list
        )

        try:
            user_summary = get_user_summary(user_id)
        except Exception:
            user_summary = "No prior memory."

        prompt = f"""You are talking with the user. Reference material below is background — use only what is directly relevant to the user's current message.

Reference DSM-5 (use ONLY if user is currently describing related symptoms):
{context_text}

User profile (background, do not recap):
{user_summary}

Recent conversation (background, do not recap):
{history_text}

Onboarding profile (background): "{questionnaire}"

User just said: "{msg}"

{STYLE_RULES}"""
        answer = (gemini.generate_content(prompt).text or "").strip()

    try:
        new_msg = {
            "user_id": user_id,
            "user_msg": msg,
            "assistant_msg": answer,
            "timestamp": time.time(),
        }
        client[MONGO_DB]["chat_history"].insert_one(new_msg)
        update_memory_lazily(user_id, history_list + [new_msg])
    except Exception as e:
        print(f"Error saving history/memory: {e}")

    return {"final_response": answer}


@app.post("/detect_video_emotions")
async def detect_video_emotions(
    user_id,
    file: UploadFile = File(...),
    client_emotions: str | None = Form(default=None),
):
    suffix = os.path.splitext(file.filename)[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        emotions, frame_count = [], 0
        if client_emotions:
            try:
                provided = json.loads(client_emotions)
                if isinstance(provided, list):
                    emotions = [str(e) for e in provided if e and e != "No face"]
            except Exception as e:
                print(f"client_emotions parse error: {e}")

        if not emotions:
            emotions, frame_count = sample_video_emotions(tmp_path, target_fps=1.0, max_frames=60)

        final_emotion = Counter(emotions).most_common(1)[0][0] if emotions else "No face detected"

        try:
            analysis = analyze_audio_ensemble(tmp_path, num_runs=3) or EMPTY_TONE
        except Exception as e:
            print(f"Tone analysis error: {e}")
            analysis = EMPTY_TONE

        try:
            transcript = transcribe_local(tmp_path)
        except Exception as e:
            print(f"Transcript error: {e}")
            transcript = ""

        if is_small_talk(transcript):
            answer = small_talk_reply(
                transcript or "(silence)",
                extra_context=f"(Their face mostly looked: {final_emotion}.)",
            )
        else:
            context_text = rag_context(transcript)
            questionnaire = fetch_questionnaire(user_id)

            prompt = f"""You are talking with the user via video. Reference material below is background — use only what's directly relevant.

Reference DSM-5 (use ONLY if user is describing related symptoms):
{context_text}

Onboarding profile (background): "{questionnaire}"

Voice tone signals: "{analysis}"
Face emotion signals: "{final_emotion}"

User just said: "{transcript}"

{STYLE_RULES}
- You may briefly acknowledge their visible emotion if it strongly contradicts their words. Otherwise don't mention it."""
            answer = (gemini.generate_content(prompt).text or "").strip()
        print(f"Final Video Response for {user_id}: {answer}")

        return JSONResponse({
            "emotions_per_frame": emotions,
            "total_frames": frame_count,
            "final_emotion": final_emotion,
            "final_response": answer,
            "audio_base64": tts_safe(answer),
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def sample_video_emotions(video_path: str, target_fps: float = 1.0, max_frames: int = 60):
    """Run DeepFace on a sampled subset of frames. Returns (emotions, frames_seen)."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return [], 0

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    stride = max(1, int(round(src_fps / target_fps)))

    emotions = []
    frame_idx = 0
    sampled = 0
    try:
        while sampled < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % stride == 0:
                emo = detect_emotion(frame)
                if emo != "No face":
                    emotions.append(emo)
                sampled += 1
            frame_idx += 1
    finally:
        cap.release()

    return emotions, frame_idx


@app.get("/process_speech")
def process_speech(userid):
    """Process all audio frames in GCS under users/{userid}/ for tone + transcript."""
    try:
        prefix = f"users/{userid}/"
        try:
            analysis, download_ms, file_count, total_bytes = speech_processor.process_gcs_frames(
                bucket_name=GCS_BUCKET, prefix=prefix
            )
        except Exception as e:
            print(f"Tone analysis error: {e}")
            analysis, download_ms, file_count, total_bytes = EMPTY_TONE, 0, 0, 0

        transcript = ""
        try:
            transcript = transcribe_latest_concat(GCS_BUCKET, k=3, pool=30, user_id=userid)
        except Exception as e:
            print(f"Voice transcript error: {e}")

        if is_small_talk(transcript):
            answer = small_talk_reply(transcript or "(silence)")
        else:
            context_text = rag_context(transcript)
            questionnaire = fetch_questionnaire(userid)

            prompt = f"""You are talking with the user via voice. Reference material below is background — use only what's directly relevant.

Reference DSM-5 (use ONLY if user is describing related symptoms):
{context_text}

Onboarding profile (background): "{questionnaire}"

Voice tone signals: "{analysis}"

User just said: "{transcript}"

{STYLE_RULES}"""
            answer = (gemini.generate_content(prompt).text or "").strip()

        return {
            "user_id": userid,
            "analysis": analysis,
            "download_ms": download_ms,
            "file_count": file_count,
            "total_bytes": total_bytes,
            "final_response": answer,
            "audio_base64": tts_safe(answer),
        }
    except Exception as e:
        print(f"Global process_speech error: {e}")
        return JSONResponse(
            {"error": "No speech recognized or processing failed", "details": str(e)},
            status_code=400,
        )


@app.post("/analyze_frame")
async def analyze_frame(file: UploadFile = File(...)):
    """Analyze a single image frame for emotion."""
    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        try:
            emotion = detect_emotion(cv2.imread(tmp_path))
        except Exception:
            emotion = "neutral"
        return {"emotion": emotion}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


class MultimodalRequest(BaseModel):
    user_id: str
    video_emotions: list[str]


@app.post("/process_multimodal")
def process_multimodal(req: MultimodalRequest):
    """Audio (GCS tone + transcript) + frontend-collected video emotions -> Gemini response + TTS."""
    userid = req.user_id
    video_emotions = req.video_emotions

    try:
        prefix = f"users/{userid}/"
        try:
            analysis, _, _, _ = speech_processor.process_gcs_frames(
                bucket_name=GCS_BUCKET, prefix=prefix
            )
        except Exception as e:
            print(f"Tone analysis error: {e}")
            analysis = EMPTY_TONE

        transcript = ""
        try:
            transcript = transcribe_latest_concat(GCS_BUCKET, k=3, pool=30, user_id=userid)
        except Exception as e:
            print(f"Voice transcript error: {e}")

        if video_emotions:
            counts = Counter(video_emotions)
            video_context = (
                f"Observed User Emotions during speech: {dict(counts)}. "
                f"Most distinctive: {counts.most_common(1)[0][0]}"
            )
        else:
            video_context = "No video data available."

        if is_small_talk(transcript):
            answer = small_talk_reply(transcript or "(silence)")
        else:
            context_text = rag_context(transcript)
            questionnaire = fetch_questionnaire(userid)

            prompt = f"""You are talking with the user via video. Reference material below is background — use only what's directly relevant.

Reference DSM-5 (use ONLY if user is describing related symptoms):
{context_text}

Onboarding profile (background): "{questionnaire}"

Voice tone signals: "{analysis}"
Face emotion signals: "{video_context}"

User just said: "{transcript}"

{STYLE_RULES}
- You may briefly acknowledge their visible emotion if it strongly contradicts their words. Otherwise don't mention it."""
            answer = (gemini.generate_content(prompt).text or "").strip()

        return {
            "user_id": userid,
            "transcript": transcript,
            "final_response": answer,
            "audio_base64": tts_safe(answer),
            "video_context": video_context,
        }
    except Exception as e:
        print(f"Multimodal error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
