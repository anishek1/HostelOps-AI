# HostelOps AI — Deployment Guide (Portfolio)

Stack: **Supabase** (DB) · **Upstash** (Redis) · **Railway** (API + Celery) · **Vercel** (Frontend)
All services have free tiers that cover this project.

---

## Prerequisites

- [ ] Supabase project created → get `DATABASE_URL` (port **5432**, not 6543)
- [ ] Upstash Redis database created → get `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` (both same `rediss://` URL)
- [ ] Groq API key → https://console.groq.com
- [ ] HuggingFace token (optional, for complaint deduplication) → https://huggingface.co/settings/tokens
- [ ] Railway account → https://railway.app
- [ ] Vercel account → https://vercel.com
- [ ] This repo pushed to GitHub

---

## Step 1 — Supabase: Enable pgvector

In your Supabase project dashboard:
1. Go to **Database → Extensions**
2. Search for `vector` and enable it

This is required before running migrations. Without it, `alembic upgrade head` will fail.

---

## Step 2 — Run Database Migrations

From your local machine with `.env` filled in:

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

Then seed the first warden account and hostel config:

```bash
python create_admin.py
```

Take note of the printed hostel code — students need it to register.

---

## Step 3 — Deploy Backend API (Railway Service 1)

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Select your repository
3. In service settings:
   - **Root Directory:** `backend`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - (Railway auto-detects `railway.toml` — this is already set)
4. Add all environment variables from `backend/.env.example`:

   | Variable | Where to get it |
   |---|---|
   | `DATABASE_URL` | Supabase → Settings → Database (port 5432) |
   | `JWT_SECRET` | Run: `openssl rand -hex 32` |
   | `GROQ_API_KEY` | https://console.groq.com |
   | `GROQ_MODEL_NAME` | `llama-3.3-70b-versatile` |
   | `CELERY_BROKER_URL` | Upstash Redis → Connect details |
   | `CELERY_RESULT_BACKEND` | Same as CELERY_BROKER_URL |
   | `ALLOWED_ORIGINS` | Your Vercel frontend URL (add after Step 5) |
   | `HF_API_KEY` | HuggingFace token (optional) |

5. Click **Deploy**. Watch logs — first deploy pulls dependencies, takes ~2 min.
6. Confirm health check: `https://your-api.railway.app/health` → `{"status":"ok"}`

---

## Step 4 — Deploy Celery Worker (Railway Service 2)

1. In the same Railway project → **New Service → GitHub Repo** (same repo)
2. Service settings:
   - **Root Directory:** `backend`
   - **Start Command:** `celery -A celery_app worker --loglevel=info --concurrency=1`
3. Copy **all the same environment variables** from Service 1 (Railway lets you reference another service's variables)
4. Deploy. Confirm in logs: `celery@... ready.`

---

## Step 5 — Deploy Celery Beat Scheduler (Railway Service 3)

1. Add another service from the same repo
2. Service settings:
   - **Root Directory:** `backend`
   - **Start Command:** `celery -A celery_app beat --loglevel=info --schedule=/tmp/celerybeat-schedule`
3. Same environment variables as above
4. Deploy. Confirm in logs: `beat: Starting...`

---

## Step 6 — Deploy Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) → **New Project → Import Git Repository**
2. Select your repo
3. In project settings:
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add environment variable:
   - `VITE_API_URL` = your Railway API URL (e.g. `https://hostelops-api.railway.app`)
     - No trailing slash
     - No `/api` suffix — the frontend code adds that
5. Deploy. Vercel gives you a URL like `hostelops-xyz.vercel.app`.

---

## Step 7 — Wire Up CORS

Now that you have the Vercel URL:

1. Go to Railway → API Service → Variables
2. Update `ALLOWED_ORIGINS`:
   ```
   https://hostelops-xyz.vercel.app
   ```
   (Add `http://localhost:5173` too if you want local dev to hit the live API)
3. Railway will auto-redeploy.

---

## Verification Checklist

- [ ] `GET https://your-api.railway.app/health` returns `{"status":"ok"}`
- [ ] `GET https://your-api.railway.app/docs` loads the Swagger UI
- [ ] Frontend loads at Vercel URL
- [ ] Can register as a student (enter hostel code from `create_admin.py` output)
- [ ] Warden can log in and approve the student
- [ ] Student can file a complaint → check Railway worker logs for AI classification running
- [ ] Celery beat logs show periodic task firing every 15 min

---

## Custom Domain (Optional)

Vercel → Project Settings → Domains → Add your domain. Free with any domain registrar.

---

## Costs

| Service | Free tier limit | Will we hit it? |
|---|---|---|
| Supabase | 500 MB DB, 2 GB bandwidth | No — portfolio traffic is tiny |
| Upstash | 10,000 commands/day | No — Celery is light |
| Railway | $5 free credit/month | 3 services × ~$0.50/month each = fine |
| Vercel | 100 GB bandwidth, 100 deployments/month | No |
