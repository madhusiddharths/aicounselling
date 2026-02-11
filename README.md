# AI-Counselling: Virtual Mental Health Companion

AI-Counselling is a virtual mental-health companion designed to support users through text, voice, and video. It leverages advanced AI to analyze facial expressions, vocal tone, and text sentiment, providing empathetic reflections, grounding exercises, and supportive guidance.

> [!IMPORTANT]
> This application is not a substitute for professional therapy. It is designed to complement care and encourage seeking licensed help when appropriate.

## 🚀 Quick Start

### 1. Prerequisites
- **Node.js** (v18+)
- **Python** (v3.10+)
- **Google Cloud CLI** (for GCS authentication)
- **MongoDB Atlas Account**
- **Clerk Account**

### 2. Backend Setup
```bash
# Navigate to the root directory
source .venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI server
python backend/main.py
```

### 3. Frontend Setup
```bash
# Install dependencies
npm install

# Start the Next.js development server
npm run dev
```

## 🛠 Tech Stack

- **Frontend**: Next.js 15, React 19, Tailwind CSS, Clerk (Auth)
- **Backend**: FastAPI, Python 3.12, Uvicorn
- **AI/ML**: Google Gemini (LLM), DeepFace (Emotion Detection), Wav2vec2 (Tone Analysis), Sentence Transformers (RAG)
- **Database**: MongoDB Atlas
- **Storage**: Google Cloud Storage (GCS)
- **Libraries**: Librosa, Pydub, PyPDF2, Faiss-cpu, OpenCV

## 🔑 Environment Variables

Create a `.env` file in the root directory and fill in the following:

```env
# MongoDB
MONGODB_URI=your_mongodb_connection_string
MONGO_DB=coach
MONGO_COLLECTION=users

# Google Cloud Storage
GCS_BUCKET=your_gcs_bucket_name
# Note: Ensure you run 'gcloud auth application-default login' locally

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_pub_key
CLERK_SECRET_KEY=your_clerk_secret_key

# Optional Storage Paths
USERS_BASE_PREFIX=users/
RECORD_SUBPATH=audio/webm/
```

## ☁️ Google Cloud Authentication

Instead of managing JSON key files, this project uses **Application Default Credentials (ADC)**. To authenticate locally:

1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install).
2. Run the following commands:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

## 📂 Project Structure

- `src/`: Next.js frontend application.
- `backend/`: FastAPI backend with AI logic and data processing.
- `backend/DSM5.pdf`: The DSM-5 manual used for context-aware counseling.
- `backend/document_embeddings.npy`: Pre-computed embeddings for RAG.
- `.venv/`: Python virtual environment.
- `requirements.txt`: Python dependencies.

## 📐 Architecture

![App Architecture](docs/architecture.png)
