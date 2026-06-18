# Deployment: Hugging Face Spaces (backend) + Vercel (frontend)

The heavy ML backend (FastAPI + Wav2Vec2 voice-tone + sentence-transformers RAG)
runs on a **Hugging Face Space** (free: 2 vCPU, 16 GB RAM, persistent, sleeps
after 48h idle). The Next.js frontend runs on **Vercel**. Face emotion is now
detected **in the browser** (face-api.js), so the backend no longer ships
TensorFlow/DeepFace/OpenCV.

---

## 1. Backend → Hugging Face Space (Docker SDK)

### Create the Space
1. https://huggingface.co/new-space → **SDK: Docker** → **Blank** template.
2. Clone it locally:
   ```bash
   git clone https://huggingface.co/spaces/<user>/<space-name> hf-space
   ```
3. **First, add a `.gitignore` to the Space repo** so secrets/cruft can never be
   committed (the Space repo does NOT inherit this project's `.gitignore`):
   ```bash
   cat > hf-space/.gitignore <<'EOF'
   # NEVER commit secrets — these go in HF Space "Secrets", not git
   .env
   *.env
   **/.env
   # build/runtime cruft
   __pycache__/
   *.pyc
   *.log
   *.webm
   EOF
   ```
4. Copy the backend deploy files into it. **`--exclude` the secrets/cruft** (the
   Dockerfile only needs `requirements.txt` + `backend/`):
   ```bash
   cp Dockerfile requirements.txt hf-space/
   rsync -a --exclude='.env' --exclude='__pycache__' \
         --exclude='*.log' --exclude='test.webm' backend/ hf-space/backend/
   ```
   > Keep `dsm5_*.json` / `dsm5_embeddings.npy` / `DSM5.pdf` — they're the prebuilt
   > RAG index. **Do not delete `DSM5.pdf`**: `rag.py` `_cache_valid()` calls
   > `os.path.getsize(DSM5.pdf)` and crashes on boot if it's missing.
5. **Track binaries with Git LFS** (HF rejects plain binary blobs). The default HF
   `.gitattributes` covers `*.npy` but **not** `*.pdf`:
   ```bash
   cd hf-space && git lfs track "*.pdf" && cd ..
   ```
6. Create `hf-space/README.md` with this HF frontmatter at the very top:
   ```markdown
   ---
   title: AI Counselling Backend
   emoji: 🧠
   colorFrom: indigo
   colorTo: purple
   sdk: docker
   app_port: 8000
   pinned: false
   ---
   ```
7. **Authenticate git for push + LFS** (HF needs a *Write* token in git's
   credential helper — `hf auth login` alone only sets the Python lib token):
   ```bash
   hf auth login --add-to-git-credential   # paste a Write token from huggingface.co/settings/tokens
   ```
   > If you get `batch response: Authorization error` on push, a stale keychain
   > cred is shadowing it — clear it and retry:
   > `printf "protocol=https\nhost=huggingface.co\n\n" | git credential-osxkeychain erase`
8. **Verify no secret is staged, THEN commit + push** — HF builds automatically:
   ```bash
   cd hf-space
   git add .
   git status --short            # <-- confirm NO ".env" appears in this list
   git lfs ls-files              # <-- should list DSM5.pdf + dsm5_embeddings.npy
   git commit -m "deploy backend" && git push origin main
   ```
   > If you see `.env` in `git status`, stop and fix the `.gitignore` — do not commit.

> The image now builds without the ~1 GB TensorFlow wheel, OpenCV, and the
> DeepFace detector models (~6–8 GB → ~2.5 GB), so builds and wake-from-idle are
> much faster.

### Set Space Secrets (Settings → Variables and secrets)
These are the **exact** env vars the backend reads:

| Secret | Required | Notes |
|--------|----------|-------|
| `GOOGLE_API_KEY` | ✅ | Gemini API key (`main.py`, `memory.py`) |
| `GCS_BUCKET` | ✅ | GCS bucket name — `speech_to_text.py` **hard-exits** if missing |
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `GCP_SA_JSON` | ✅ | **Full contents** of the Google service-account JSON (one secret). `entrypoint.sh` writes it to `/tmp/gcp-sa.json` and points GCS + TTS auth at it. |
| `MONGO_DB` | optional | defaults to `coach` |
| `MONGO_COLLECTION` | optional | defaults to `users` |
| `USERS_BASE_PREFIX` | optional | defaults to `users/` |
| `RECORD_SUBPATH` | optional | defaults to `audio/webm/` |

> Do **not** set `TTS_CREDENTIALS` or `GOOGLE_APPLICATION_CREDENTIALS` manually —
> `entrypoint.sh` derives both from `GCP_SA_JSON` at startup.

Your Space URL will be `https://<user>-<space-name>.hf.space`. Hit `/` to confirm
the health check returns `{"status": "ok", ...}`.

---

## 2. Frontend → Vercel

1. Import the GitHub repo into Vercel (Next.js is auto-detected; `vercel.json` is
   already present).
2. Set environment variables (Project → Settings → Environment Variables):

   | Var | Value |
   |-----|-------|
   | `NEXT_PUBLIC_FASTAPI_BASE_URL` | your Space URL, e.g. `https://<user>-<space>.hf.space` |
   | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | from Clerk |
   | `CLERK_SECRET_KEY` | from Clerk |
   | `MONGODB_URI` | same Mongo connection string |
   | (any GCS creds your `/api/audio` + `/api/uploadVideo` routes use) | |

   > `NEXT_PUBLIC_FASTAPI_BASE_URL` is **inlined into the JS bundle at build
   > time** — after changing it you must **redeploy**, not just restart.

3. Deploy. The browser will call the Space directly; the backend already sends
   `Access-Control-Allow-Origin: *` (`main.py` CORS middleware), so cross-origin
   calls from the Vercel domain work out of the box.

---

## 3. Credentials note

`gen-lang-client-...json` (a Google **service-account key**) sits in the repo
root as a plaintext file. Good news: it is already in `.gitignore` and was
**never committed** (verified — not tracked, not in history), so it won't leak
via the repo.

For deploy, don't upload the file — paste its contents into the `GCP_SA_JSON`
Space secret (section 1). It can't be baked into the image anyway: the Dockerfile
only copies `requirements.txt` + `backend/`, never the root key file.
