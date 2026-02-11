# Project Structure Guide

## Directory Organization

```
ai-counselling/
├── .env.example              # Example environment variables (commit this)
├── .gitignore                # Git ignore rules
├── .git/                      # Git repository
│
├── README.md                  # Main project documentation
├── DEPLOYMENT.md              # Deployment guide for all platforms
├── CONTRIBUTING.md            # Contributing guidelines
│
├── Dockerfile                 # Docker configuration for backend
├── Dockerfile.frontend        # Docker configuration for frontend
├── docker-compose.yml         # Docker Compose for local development
├── vercel.json                # Vercel deployment configuration
│
├── package.json               # Node.js dependencies
├── package-lock.json          # Locked npm versions
├── tsconfig.json              # TypeScript configuration
├── next.config.ts             # Next.js configuration
├── eslint.config.mjs          # ESLint configuration
├── postcss.config.mjs         # PostCSS configuration
├── next-env.d.ts              # Next.js TypeScript definitions
│
├── requirements.txt           # Python dependencies
│
├── src/                       # Next.js/React Frontend
│   ├── middleware.ts          # Next.js middleware
│   ├── app/
│   │   ├── page.tsx           # Home page
│   │   ├── layout.tsx         # Root layout
│   │   ├── globals.css        # Global styles
│   │   ├── favicon.ico        # Favicon
│   │   ├── components/        # React components
│   │   │   ├── Navbar.tsx
│   │   │   ├── Hero.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── Pricing.tsx
│   │   │   ├── Programs.tsx
│   │   │   ├── ModeToggle.tsx
│   │   │   ├── VideoRecorder.tsx
│   │   │   ├── VoiceCircle.tsx
│   │   │   ├── CTASection.tsx
│   │   │   ├── DebugUserConsole.tsx
│   │   │   └── chat/          # Chat components
│   │   │       ├── ChatPane.tsx
│   │   │       ├── ChatComposer.tsx
│   │   │       └── MessageBubble.tsx
│   │   ├── api/               # API routes
│   │   │   ├── audio/         # Audio upload endpoint
│   │   │   ├── uploadVideo/   # Video upload endpoint
│   │   │   └── webhooks/      # Webhook handlers
│   │   │       └── clerk/     # Clerk authentication webhooks
│   │   ├── actions/           # Server actions
│   │   │   └── preferences.ts
│   │   ├── onboarding/        # Onboarding flow
│   │   ├── record/            # Recording page
│   │   └── sign-in/           # Authentication pages
│   ├── db/                    # Database utilities
│   │   ├── users.ts           # User database functions
│   │   └── audio.ts           # Audio database functions
│   ├── hooks/                 # React hooks
│   │   └── useAudioChunkUploader.tsx
│   └── lib/                   # Utility libraries
│       └── mongo.ts           # MongoDB connection
│
├── public/                    # Static assets
│   ├── logo.png
│   ├── heroSunset.png
│   ├── next.svg
│   ├── vercel.svg
│   └── (other assets)
│
├── backend/                   # FastAPI Backend
│   ├── main.py               # Main FastAPI application
│   ├── speech_to_text.py      # Speech-to-text processing
│   ├── process_audio_tone.py  # Audio tone analysis
│   ├── mongodb_fetcher.py     # MongoDB helper functions
│   ├── DSM5.pdf               # DSM-5 reference document
│   └── document_embeddings.npy # Pre-computed embeddings for RAG
│
├── run_emotion_analysis.py    # Standalone emotion analysis script
├── test_emotion_recognition.py # Emotion recognition tests

```

## Key Files Explained

### Configuration Files
- **`.env.example`** - Template for environment variables. Copy to `.env` and fill in actual values.
- **`.gitignore`** - Specifies files to exclude from git (credentials, node_modules, etc.)
- **`package.json`** - Node.js project metadata and dependencies
- **`requirements.txt`** - Python package dependencies
- **`tsconfig.json`** - TypeScript compiler configuration
- **`next.config.ts`** - Next.js framework configuration

### Deployment Files
- **`Dockerfile`** - Container definition for Python backend (FastAPI)
- **`Dockerfile.frontend`** - Container definition for Node.js frontend (Next.js)
- **`docker-compose.yml`** - Multi-container orchestration for local development
- **`vercel.json`** - Vercel deployment configuration (frontend hosting)

### Documentation
- **`README.md`** - Project overview, features, and quick start
- **`DEPLOYMENT.md`** - Detailed deployment instructions for different platforms
- **`CONTRIBUTING.md`** - Guidelines for contributors

## Frontend Structure (Next.js)

- **App Router** (`src/app/`) - Page-based routing
- **Components** - Reusable React components with TypeScript
- **Hooks** - Custom React hooks for logic
- **Lib** - Utility functions and database helpers
- **API Routes** - RESTful endpoints for backend integration
- **Database Models** - TypeScript utilities for database operations

## Backend Structure (FastAPI)

- **main.py** - Entry point with API endpoints
- **speech_to_text.py** - Speech recognition processing
- **process_audio_tone.py** - Emotional tone analysis from audio
- **mongodb_fetcher.py** - Database query helpers
- **Static Assets** - Pre-computed embeddings and reference documents

## Getting Started

1. **Setup Local Development**
   ```bash
   # Install dependencies
   npm install
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your credentials
   
   # Run development servers
   npm run dev          # Terminal 1: Frontend on :3000
   python backend/main.py  # Terminal 2: Backend on :8000
   ```

2. **Deploy to Production**
   - **Frontend**: Push to GitHub → Auto-deploy to Vercel
   - **Backend**: Deploy to Railway, Render, or your preferred platform
   - See `DEPLOYMENT.md` for detailed instructions

3. **Contributing**
   - Read `CONTRIBUTING.md`
   - Create a feature branch
   - Submit a pull request

## Important Notes

- The project uses **Clerk** for authentication
- **MongoDB Atlas** for database
- **Google Cloud Storage** for file uploads
- **Vercel** for frontend hosting
- **FastAPI** serves as the AI processing backend

## What to Delete Before Upload

- ✅ `.env` (actual secrets - keep `.env.example`)
- ✅ `node_modules/` (regenerated from package-lock.json)
- ✅ `.next/` (build output)
- ✅ `__pycache__/` (Python cache)
- ✅ `.venv/` or `venv/` (virtual environment)
- ✅ IDE folders (`.vscode/`, `.idea/`)

All of the above are already in `.gitignore` so they won't be committed.

## What's Important to Commit

- ✅ All source code (src/, backend/)
- ✅ Configuration files (package.json, requirements.txt, etc.)
- ✅ Deployment configs (Dockerfile, docker-compose.yml, vercel.json)
- ✅ Documentation (README.md, DEPLOYMENT.md, CONTRIBUTING.md)
- ✅ `.env.example` (example only, not secrets)
- ✅ `.gitignore` (excludes sensitive files automatically)

---

This structure is now ready for uploading to GitHub and deploying from the main branch!

