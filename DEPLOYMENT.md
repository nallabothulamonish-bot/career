# Deployment Guide (Render + Vercel)

## 1. Database — Render MySQL (or PlanetScale / any managed MySQL 8+)
1. Create a MySQL instance on Render (or your provider of choice).
2. Note the connection string, e.g.
   `mysql+pymysql://user:password@host:3306/careerpilot`

## 2. Backend — Render Web Service
1. Push this repo to GitHub.
2. On Render: New → Web Service → connect your repo, root directory `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (from `.env.example`):
   - `DATABASE_URL`
   - `JWT_SECRET`
   - `CLIENT_ORIGIN` → your Vercel frontend URL (set after step 3)
   - `ANTHROPIC_API_KEY` (optional, for LLM-generated interview Q&A)
6. Deploy. Tables auto-create on first startup. Optionally run the seed script
   via Render's shell: `python -m app.seed.seed`

## 3. Frontend — Vercel
1. On Vercel: New Project → import the repo, root directory `frontend/`.
2. Framework preset: Vite.
3. Environment variable: `VITE_API_URL=https://<your-render-backend>.onrender.com/api`
4. Deploy.
5. Go back to Render and set `CLIENT_ORIGIN` to your Vercel domain, then redeploy
   the backend so CORS allows it.

## 4. Git & GitHub workflow
```bash
git init
git add .
git commit -m "Initial commit: CareerPilot AI platform"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```
Use feature branches + PRs for subsequent changes; both Render and Vercel can
auto-deploy on push to `main`.
