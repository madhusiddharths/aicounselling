# Quick Reference: Deploy to GitHub

## The Commands You Need

### Step 1: Set Up Git Remote (One Time)
```bash
cd /Users/madhusiddharthsuthagar/Documents/python/mhacks

# Remove any old origin
git remote remove origin 2>/dev/null || true

# Add your GitHub repository (replace URL)
git remote add origin https://github.com/YOUR_USERNAME/ai-counselling.git

# Verify remote is set
git remote -v
```

### Step 2: Prepare Main Branch
```bash
# Switch to/create main branch
git branch -M main

# Verify you're on main
git branch
```

### Step 3: Commit All Staged Changes
```bash
# All files are already staged. Commit them:
git commit -m "Initial commit: AI Counselling project with Docker, Vercel, and deployment configs"
```

### Step 4: Push to GitHub
```bash
# Push to GitHub
git push -u origin main

# Verify it's there
git log --oneline | head -3
```

## Quick Verification Commands

```bash
# Check what will be committed
git status

# See how many files are ready
git diff --cached --name-only | wc -l

# Check git configuration
git config --list | grep -E "user|remote"

# View recent commits
git log --oneline -5
```

## Environment Setup (After Push)

1. **Create `.env` file** (not committed, for local dev)
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. **Install dependencies**
   ```bash
   npm install
   pip install -r requirements.txt
   ```

3. **Run locally**
   ```bash
   # Terminal 1
   npm run dev
   
   # Terminal 2
   python backend/main2.py
   ```

## Deployment Platforms

### Vercel (Frontend)
1. Go to [vercel.com](https://vercel.com)
2. Click "Import Project"
3. Select your GitHub repo
4. Add environment variables from `.env`
5. Click "Deploy"

### Railway (Backend)
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select your GitHub repo
4. Add MongoDB plugin
5. Add environment variables
6. Deploy

### MongoDB Atlas (Database)
1. Create account at [mongodb.com](https://mongodb.com)
2. Create cluster
3. Copy connection string to `.env` as `MONGODB_URI`

## Troubleshooting

### "Nothing to commit"
→ All files are already added. Run: `git status`

### "fatal: not a git repository"
→ You're in the wrong directory. Run: `cd /Users/madhusiddharthsuthagar/Documents/python/mhacks`

### "error: refusing to merge unrelated histories"
→ Use `git push -u origin main --force` (only for first push)

### Secrets accidentally committed?
→ See `DEPLOYMENT.md` for how to fix
→ Always use `.env` (not `.env.example`) for secrets

## File Checklist

Before pushing, verify these are NOT in git:
- [ ] `.env` (actual secrets)
- [ ] `node_modules/`
- [ ] `.next/`
- [ ] `__pycache__/`
- [ ] `.venv/`

Verify these ARE in git:
- [ ] `src/` directory
- [ ] `backend/` directory
- [ ] `package.json`
- [ ] `requirements.txt`
- [ ] `Dockerfile`
- [ ] `docker-compose.yml`
- [ ] `vercel.json`
- [ ] `.env.example`
- [ ] `.gitignore`
- [ ] `README.md`

## What to Do After Push

1. **GitHub**: Verify files appear in web interface
2. **Vercel**: Import repo and deploy frontend
3. **Railway**: Create project and deploy backend
4. **Local**: Update `.env` and test locally
5. **Verify**: Test all features in development

## Support Files

- **README.md** - Start here for project info
- **DEPLOYMENT.md** - Full deployment guide
- **CONTRIBUTING.md** - For team collaboration
- **PROJECT_STRUCTURE.md** - Directory structure
- **SETUP_COMPLETE.md** - Setup confirmation
- **.env.example** - Environment variables template

---

**All 64+ files are staged and ready to go! Just run the commands above to push to GitHub.** 🚀

