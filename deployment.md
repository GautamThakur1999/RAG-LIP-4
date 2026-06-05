# Deployment Guide — Railway (Backend) + Vercel (Frontend)

This document provides step-by-step instructions to deploy the ICICI Prudential FAQ Assistant as two separate services:

- **Backend API** → [Railway](https://railway.app) (Python / FastAPI)
- **Frontend UI** → [Vercel](https://vercel.com) (Next.js)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Pre-Deployment Code Changes](#2-pre-deployment-code-changes)
3. [Deploy Backend to Railway](#3-deploy-backend-to-railway)
4. [Deploy Frontend to Vercel](#4-deploy-frontend-to-vercel)
5. [Post-Deployment Verification](#5-post-deployment-verification)
6. [Environment Variables Reference](#6-environment-variables-reference)
7. [Troubleshooting](#7-troubleshooting)
8. [Architecture Diagram](#8-architecture-diagram)

---

## 1. Prerequisites

Before you begin, ensure you have:

- [ ] A [GitHub account](https://github.com) with the repo pushed to `https://github.com/GautamThakur1999/RAG-LIP-4.git`
- [ ] A [Railway account](https://railway.app) (free Hobby plan or paid)
- [ ] A [Vercel account](https://vercel.com) (free Hobby plan is fine)
- [ ] A valid **Groq API Key** (get one at <https://console.groq.com>)
- [ ] Node.js 18+ installed locally (for testing frontend builds)
- [ ] Python 3.11+ installed locally (for testing backend)

---

## 2. Pre-Deployment Code Changes

> [!IMPORTANT]
> Most of the code-side wiring is **already in place** in this repo (env-based API URL, dynamic `$PORT`, env-based CORS, health endpoint, `Procfile`, `runtime.txt`). The steps below are mostly **verification** — confirm each is present before deploying. Only §2.5 (slim requirements build) requires a new action.

### 2.1 Frontend: API URL is env-based ✅ (verify)

The frontend already reads the backend URL from `NEXT_PUBLIC_API_URL`, with a localhost fallback for local dev. Confirm both files look like this:

#### `frontend/src/app/chat/page.tsx`

```ts
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const response = await fetch(`${apiUrl}/api/chat`, { ... });
```

#### `frontend/src/app/sources/page.tsx`

```ts
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
fetch(`${apiUrl}/api/sources`)
```

For local development you may optionally create `frontend/.env.local`:

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> [!NOTE]
> The `NEXT_PUBLIC_` prefix is required by Next.js to expose the variable to the browser **at build time**. If you change it on Vercel you must **redeploy** (not just restart) for it to take effect.

### 2.2 Backend: binds to Railway's `$PORT` ✅ (verify)

`app/api.py` already reads the dynamic port, and the `Procfile` (the actual production entrypoint) passes `$PORT` to uvicorn. The `__main__` block is only for local runs:

```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.api:app", host="0.0.0.0", port=port)
```

> In production Railway does **not** run this block — it runs the `Procfile` command (`uvicorn app.api:app --host 0.0.0.0 --port $PORT`). The `$PORT` binding is what matters, and it's handled.

### 2.3 Backend: CORS is env-based ✅ (verify)

`app/api.py` already builds its allow-list from `FRONTEND_URL`, so no `["*"]` is shipped:

```python
frontend_url = os.environ.get("FRONTEND_URL", "")
allowed_origins = ["http://localhost:3000"]
if frontend_url:
    allowed_origins.append(frontend_url)
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, ...)
```

Just set `FRONTEND_URL` on Railway after the Vercel deploy (Step 6 in §4).

> [!TIP]
> **Vercel preview deployments** get rotating URLs like `https://rag-lip-4-git-<branch>-<user>.vercel.app`, which won't match a single `FRONTEND_URL` and will be **blocked by CORS**. If you want previews to work, additionally pass `allow_origin_regex=r"https://.*\.vercel\.app"` to the `CORSMiddleware`. For production-only, the single `FRONTEND_URL` is enough.

### 2.4 Backend: health endpoint ✅ (verify)

`app/api.py` exposes `GET /` returning `{"status": "ok", ...}`. Use this as Railway's healthcheck path (§3, Step 2) and for uptime probes — it's lighter and more reliable than hitting `/docs`.

### 2.5 Ensure data files are committed to Git

The backend needs these files at runtime. They are NOT in `.gitignore`, but double-check they exist in your repo:

| File/Directory | Purpose | Must be in Git? |
|---|---|---|
| `data/bm25_index.pkl` | BM25 sparse search index | ✅ Yes |
| `data/sources.csv` | Source URLs for Source Hub | ✅ Yes |
| `data/processed/*.txt` | Parsed text files | ✅ Yes |
| `data/processed/chunks.jsonl` | Chunked documents | ✅ Yes |
| `data/manifest.json` | Fetch manifest | ✅ Yes |
| `chroma_db/` | Vector DB (not used in prod) | ❌ No (in .gitignore) |
| `data/raw/` | Raw HTML cache | ❌ No (in .gitignore) |
| `.env` | Secrets | ❌ No (in .gitignore) |

### 2.6 `Procfile` for Railway ✅ (verify)

Confirm a file named `Procfile` (no extension) exists in the project root with:

```
web: uvicorn app.api:app --host 0.0.0.0 --port $PORT
```

### 2.7 `runtime.txt` for Railway Python version ✅ (verify)

Confirm `runtime.txt` exists in the project root with:

```
python-3.11.12
```

### 2.8 ⚠️ Use the slim requirements for the Railway build (REQUIRED action)

> [!WARNING]
> This is the one step you must actively do. By default Railway installs the full `requirements.txt`, which includes `torch` + `sentence-transformers` + `chromadb` + `streamlit` (~2 GB). On the Hobby plan this causes very slow builds and often an **out-of-memory build failure**. The deployed backend does **not** need any of those — retrieval is BM25-only and the index is pre-built and committed.

A slim `requirements-deploy.txt` is already in the repo:

```
requests
beautifulsoup4
langchain-text-splitters
rank-bm25
pydantic-settings
python-dotenv
groq
fastapi
uvicorn
```

This is the exact runtime set the backend imports (`fastapi`, `uvicorn`, `groq`, `rank-bm25` to unpickle the BM25 index, `pydantic-settings` for config). **No `chromadb` / `torch` / `sentence-transformers` is imported at runtime** — `src/retrieve/retriever.py` is intentionally BM25-only.

Tell Railway to use it. Two options (pick one):

**Option A — Custom Build Command (simplest).** In Railway → service → **Settings → Build**, set the Build Command to:

```
pip install -r requirements-deploy.txt
```

**Option B — `nixpacks.toml` (committed, reproducible).** Add this file to the project root:

```toml
[phases.install]
cmds = ["pip install -r requirements-deploy.txt"]
```

> [!NOTE]
> A `Procfile` controls the **runtime** start command only — it cannot change what gets **installed**. Use the Build Command or `nixpacks.toml` above to control installation.

### 2.9 Push all changes to GitHub

```bash
git add .
git commit -m "Prepare for Railway + Vercel deployment (slim build, health endpoint)"
git push origin main
```

---

## 3. Deploy Backend to Railway

### Step 1: Create a new Railway project

1. Go to [railway.app](https://railway.app) and log in.
2. Click **"New Project"** → **"Deploy from GitHub Repo"**.
3. Select `GautamThakur1999/RAG-LIP-4`.
4. Railway will auto-detect the `Procfile` and a `requirements*.txt`.

### Step 2: Configure the Railway service

1. Click on the deployed service → **Settings** tab.
2. Under **"Root Directory"**, leave it as `/` (the project root).
3. Under **"Build Command"**, set it to **`pip install -r requirements-deploy.txt`** (see §2.8 — do not let it default to the heavy `requirements.txt`). Skip this if you added `nixpacks.toml`.
4. Under **"Start Command"**, verify it shows: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`.
5. Under **Settings → Deploy → Healthcheck Path**, set it to **`/`** (the health endpoint added in §2.4).

### Step 3: Set environment variables

Go to the **Variables** tab and add:

| Variable | Value | Required |
|---|---|---|
| `GROQ_API_KEY` | `gsk_your_actual_key_here` | ✅ |
| `FRONTEND_URL` | `https://your-app.vercel.app` | ✅ (set after Vercel deploy) |

> [!NOTE]
> `SCORE_THRESHOLD`, `TOP_K`, and `LLM_MODEL` are **not** currently read from the environment — they are hardcoded in `src/retrieve/retriever.py` and `src/llm/client.py`. Setting them as Railway variables has no effect today. To change them, edit those files (or wire them to `config.settings` first). See §6.

### Step 4: Generate a public URL

1. Go to **Settings** → **Networking**.
2. Click **"Generate Domain"** to get a public Railway URL.
3. Your backend will be accessible at something like:

   ```
   https://rag-lip-4-production.up.railway.app
   ```

4. **Copy this URL** — you'll need it for the Vercel frontend.

### Step 5: Verify the backend is running

First hit the health endpoint:

```
https://YOUR-RAILWAY-URL/
```

This should return `{"status":"ok","retriever_ready":true,"llm_ready":true}`. If `retriever_ready` is `false`, the BM25 index files didn't make it into Git (see §2.5); if `llm_ready` is `false`, `GROQ_API_KEY` is missing.

Then open the Swagger docs:

```
https://YOUR-RAILWAY-URL/docs
```

This should show the `/api/chat` and `/api/sources` endpoints.

Also test the sources endpoint directly:

```
https://YOUR-RAILWAY-URL/api/sources
```

This should return a JSON array of mutual fund sources.

---

## 4. Deploy Frontend to Vercel

### Step 1: Import the project

1. Go to [vercel.com](https://vercel.com) and log in.
2. Click **"Add New..."** → **"Project"**.
3. Import `GautamThakur1999/RAG-LIP-4` from GitHub.

### Step 2: Configure the project settings

> [!IMPORTANT]
> This is the most critical step. You MUST set the Root Directory to `frontend`, otherwise Vercel will try to build the Python backend and fail.

| Setting | Value |
|---|---|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `.next` (default) |
| **Install Command** | `npm install` (default) |

### Step 3: Set environment variables

In the Vercel project settings → **Environment Variables**, add:

| Variable | Value | Environment |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-RAILWAY-URL` | Production, Preview, Development |

> [!WARNING]
> Do NOT include a trailing slash in the URL. Use `https://rag-lip-4-production.up.railway.app` not `https://rag-lip-4-production.up.railway.app/`.

### Step 4: Deploy

Click **"Deploy"**. Vercel will:

1. Clone the repo
2. Navigate to the `frontend/` directory
3. Run `npm install`
4. Run `npm run build`
5. Deploy the static + serverless output

### Step 5: Note your Vercel URL

After deployment, Vercel will give you a URL like:

```
https://rag-lip-4.vercel.app
```

### Step 6: Update Railway CORS with the Vercel URL

Go back to your Railway project → **Variables** tab → set:

```
FRONTEND_URL=https://rag-lip-4.vercel.app
```

Railway will auto-redeploy with the updated CORS whitelist.

---

## 5. Post-Deployment Verification

### Checklist

- [ ] **Backend health**: Visit `https://YOUR-RAILWAY-URL/` — returns `{"status":"ok","retriever_ready":true,"llm_ready":true}`
- [ ] **Swagger**: Visit `https://YOUR-RAILWAY-URL/docs` — UI loads
- [ ] **Sources API**: Visit `https://YOUR-RAILWAY-URL/api/sources` — returns JSON array
- [ ] **Frontend home**: Visit `https://YOUR-VERCEL-URL` — home page renders with sidebar
- [ ] **Frontend chat**: Click "Chat" → ask "What is the exit load for the Technology fund?" → get a factual response with citation
- [ ] **Frontend sources**: Click "Source Hub" → cards render with category labels
- [ ] **Guardrail test**: Ask "Should I invest in the Technology fund?" → get a refusal response
- [ ] **PII test**: Ask "My PAN is ABCDE1234F" → get a PII block response
- [ ] **CORS check**: Open browser DevTools → Network tab → no CORS errors on API calls

### Common Issues at This Stage

| Symptom | Cause | Fix |
|---|---|---|
| Chat shows "Could not connect to API" | `NEXT_PUBLIC_API_URL` not set or wrong | Check Vercel env vars, redeploy |
| CORS error in browser console | `FRONTEND_URL` not set on Railway | Add `FRONTEND_URL` env var on Railway |
| Sources page shows error | Railway backend not fully started | Wait 30s and retry, check Railway logs |
| "GROQ_API_KEY not set" in chat | Missing env var on Railway | Add `GROQ_API_KEY` in Railway Variables |
| Build fails on Vercel | Root directory not set to `frontend` | Change Root Directory in Vercel settings |
| `ModuleNotFoundError` on Railway | Build used wrong requirements file | Ensure Build Command is `pip install -r requirements-deploy.txt` (§2.8); add the missing package there and push |
| Railway build OOM / very slow | Heavy `requirements.txt` (torch/chromadb) installed | Use the slim `requirements-deploy.txt` build (§2.8) |
| Health shows `retriever_ready:false` | BM25 index not committed | Confirm `data/bm25_index.pkl` + `data/processed/chunks.jsonl` are in Git (§2.5) |
| Vercel preview URL gets CORS error | Single `FRONTEND_URL` doesn't match preview domain | Add `allow_origin_regex=r"https://.*\.vercel\.app"` (§2.3) |

---

## 6. Environment Variables Reference

### Backend (Railway)

| Variable | Description | Default | Required |
|---|---|---|---|
| `GROQ_API_KEY` | Groq LLM API key (read via `os.getenv` fallback in `client.py`) | — | ✅ |
| `PORT` | Server port (auto-set by Railway) | `8000` | Auto |
| `FRONTEND_URL` | Vercel frontend URL for CORS allow-list | `""` | ✅ |

> [!IMPORTANT]
> **Not currently env-configurable.** `LLM_MODEL` is hardcoded to `llama-3.3-70b-versatile` in `src/llm/client.py` (comment: *"Hardcoded to bypass env caching"*), and `TOP_K` (5) / `SCORE_THRESHOLD` (0.35) are module constants in `src/retrieve/retriever.py`. `MAX_SENTENCES` lives in `config.py` but isn't enforced from env either. Setting these as Railway variables does nothing today — change the values in code, or refactor them to read from `config.settings` if you want runtime control.

### Frontend (Vercel)

| Variable | Description | Default | Required |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Full Railway backend URL (no trailing slash) | — | ✅ |

---

## 7. Troubleshooting

### Railway build takes too long / fails with OOM

`sentence-transformers` and `torch` are large packages (~2GB). If Railway's free tier runs out of memory during install:

This is handled by the slim build in **§2.8** — the deployed backend is BM25-only and never imports `sentence-transformers`, `torch`, `chromadb`, or `streamlit` at runtime, so `requirements-deploy.txt` excludes them.

Set Railway's **Build Command** (Settings → Build) to:

```
pip install -r requirements-deploy.txt
```

or commit a `nixpacks.toml` with the same install command (see §2.8 Option B).

> [!CAUTION]
> A **`Procfile` cannot change what gets installed** — it only sets the runtime start command. Use the Build Command or `nixpacks.toml`. If the build still pulls torch, the Build Command didn't take effect.

### Frontend fetch fails in production but works locally

This is almost always because `NEXT_PUBLIC_API_URL` is not set on Vercel. Remember:

- `NEXT_PUBLIC_` variables are **baked in at build time** in Next.js.
- If you add/change the variable, you **must redeploy** (not just restart).

### Railway deploys but API returns 500

Check Railway logs for the exact Python traceback. Common causes:

- `data/bm25_index.pkl` is not in the git repo (check `.gitignore`)
- `GROQ_API_KEY` environment variable is missing or invalid

---

## 8. Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    User Browser                      │
│                                                      │
│   ┌────────────────────────────────────────────┐     │
│   │         Vercel (Next.js Frontend)          │     │
│   │         https://your-app.vercel.app        │     │
│   │                                            │     │
│   │  Home Page  │  Chat Page  │  Source Hub     │     │
│   └────────────────────┬───────────────────────┘     │
│                        │ HTTPS (fetch)               │
│                        ▼                             │
│   ┌────────────────────────────────────────────┐     │
│   │       Railway (FastAPI Backend)            │     │
│   │       https://your-api.up.railway.app      │     │
│   │                                            │     │
│   │  POST /api/chat   │  GET /api/sources      │     │
│   │       │                                    │     │
│   │       ▼                                    │     │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │     │
│   │  │PII Guard │→ │Intent    │→ │BM25      │ │     │
│   │  │          │  │Guard     │  │Retriever │ │     │
│   │  └──────────┘  └──────────┘  └────┬─────┘ │     │
│   │                                   │       │     │
│   │                              ┌────▼─────┐ │     │
│   │                              │Groq LLM  │ │     │
│   │                              │(llama-3) │ │     │
│   │                              └──────────┘ │     │
│   └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## Quick Reference Commands

```bash
# Local development (both services)
# Terminal 1: Backend
cd "RAG LIP 4"
.venv\Scripts\activate
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd "RAG LIP 4/frontend"
npm run dev

# Push deployment changes
git add .
git commit -m "Deploy to Railway + Vercel"
git push origin main
```
