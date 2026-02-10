# Deployment Guide

This guide covers deploying the AI-Counselling application to various platforms.

## Table of Contents
- [Local Development](#local-development)
- [Vercel (Frontend)](#vercel-frontend)
- [Railway/Render (Backend)](#railwayrender-backend)
- [Docker Deployment](#docker-deployment)

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.10+
- MongoDB (local or Atlas)
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-counselling
   ```

2. **Install dependencies**
   ```bash
   # Frontend
   npm install
   
   # Backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

4. **Run the application**
   ```bash
   # Terminal 1: Frontend
   npm run dev
   
   # Terminal 2: Backend
   python backend/main2.py
   ```

The application will be available at `http://localhost:3000`

---

## Vercel (Frontend)

### Deployment Steps

1. **Create Vercel Account**
   - Visit [vercel.com](https://vercel.com) and sign up

2. **Connect Repository**
   - Import your GitHub/GitLab repository
   - Select the root directory as the project root

3. **Configure Environment Variables**
   - Add all `NEXT_PUBLIC_*` variables from `.env.example`:
     - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
     - `NEXT_PUBLIC_CLERK_SIGN_IN_URL`
     - `NEXT_PUBLIC_CLERK_SIGN_UP_URL`
     - `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`
     - `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`

4. **Add Secret Variables**
   - Add secret environment variables (visible only in backend):
     - `CLERK_SECRET_KEY`
     - `MONGODB_URI`
     - `GOOGLE_GENERATIVE_AI_API_KEY`
     - Other sensitive keys

5. **Deploy**
   - Click "Deploy" - Vercel will automatically deploy on every push to main

### Post-Deployment
- Update your custom domain in Vercel settings
- Configure Clerk to use the Vercel URL as allowed origin

---

## Railway/Render (Backend)

### Using Railway (Recommended for FastAPI)

1. **Create Railway Account**
   - Visit [railway.app](https://railway.app)

2. **Create New Project**
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository

3. **Configure Service**
   - Set root directory if needed
   - Add environment variables from `.env.example`

4. **MongoDB Setup**
   - In Railway, create a new MongoDB plugin
   - It will automatically populate `MONGODB_URI`

5. **Deploy**
   - Railway will auto-detect and deploy your Python app
   - Set the start command if needed: `uvicorn backend.main2:app --host 0.0.0.0 --port $PORT`

### Verifying Backend Deployment
```bash
curl https://your-railway-app.up.railway.app/docs
```

---

## Docker Deployment

### Build Docker Images

1. **Build Backend**
   ```bash
   docker build -f Dockerfile -t ai-counselling-backend:latest .
   ```

2. **Build Frontend**
   ```bash
   docker build -f Dockerfile.frontend -t ai-counselling-frontend:latest .
   ```

### Run with Docker Compose

```bash
docker-compose up -d
```

This will start:
- MongoDB on `mongodb://mongodb:27017`
- Backend on `http://localhost:8000`
- Frontend on `http://localhost:3000`

### Docker Hub / Container Registry

1. **Tag your images**
   ```bash
   docker tag ai-counselling-backend:latest <your-registry>/ai-counselling-backend:latest
   docker tag ai-counselling-frontend:latest <your-registry>/ai-counselling-frontend:latest
   ```

2. **Push to registry**
   ```bash
   docker push <your-registry>/ai-counselling-backend:latest
   docker push <your-registry>/ai-counselling-frontend:latest
   ```

---

## Production Checklist

- [ ] All environment variables configured
- [ ] Database backups enabled
- [ ] SSL/HTTPS enabled
- [ ] CORS properly configured
- [ ] API rate limiting enabled
- [ ] Logging and monitoring set up
- [ ] Health checks configured
- [ ] Database indices created
- [ ] Security headers configured
- [ ] Sensitive data encrypted

---

## Troubleshooting

### Backend not connecting to MongoDB
- Verify `MONGODB_URI` is correct
- Check MongoDB credentials
- Ensure IP is whitelisted (for MongoDB Atlas)

### Clerk authentication failing
- Verify `CLERK_SECRET_KEY` and `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- Check allowed origins/domains in Clerk dashboard
- Clear browser cookies and try again

### File uploads failing
- Verify Google Cloud Storage credentials
- Check bucket name in environment variables
- Ensure service account has proper permissions

### Timeout errors
- Increase function timeout in `vercel.json` for longer operations
- Check backend logs for slow queries
- Optimize database queries

---

## Support

For issues or questions, please create an issue in the GitHub repository.

