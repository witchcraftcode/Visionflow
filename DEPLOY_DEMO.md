# Live Demo Deployment (Vercel + Render)

VisionFlow isn't a fit for Vercel on its own: predictions run through a
**Redis-backed job queue and a separate worker process** (see `app/queue` and
`app/worker`), and the models are loaded once into a long-lived process — none
of that runs inside Vercel's stateless serverless functions. Vercel is a great
fit for the **frontend** (already built in `frontend/`, with upload/predict,
`StatsGrid`, and `Architecture` components). The **API + worker + Redis**
need a host that runs persistent processes — this repo already ships a
`render.yaml` for exactly that.

So the live demo is two small deploys, wired together with one env var.

## 1. Push to GitHub
Both Render and Vercel deploy from a GitHub repo.
```bash
cd Visionflow-main
git init   # skip if already a git repo
git add -A
git commit -m "Prep for live demo deploy"
gh repo create visionflow --public --source=. --push   # or push to an existing remote
```

## 2. Backend: Render (uses the existing render.yaml)
1. Go to https://dashboard.render.com -> **New** -> **Blueprint**.
2. Pick your `visionflow` repo. Render reads `render.yaml` and proposes 3
   services: `visionflow-redis`, `visionflow-api` (web), `visionflow-worker`.
3. Click **Apply**. First build takes a few minutes (installs onnxruntime,
   copies the bundled ONNX models under `app/models/onnx/`).
4. Once `visionflow-api` is live, copy its URL, e.g.
   `https://visionflow-api.onrender.com`, and confirm it works:
```bash
   curl https://visionflow-api.onrender.com/health
```
   Note: Render's free/starter web services spin down when idle, so the
   first request after a quiet period can take 30-60s to wake up — normal
   for a demo, worth a small "waking up the model server..." message in the UI
   if you want to be polished about it.

## 3. Frontend: Vercel
1. Go to https://vercel.com/new, import the same repo.
2. Set **Root Directory** to `frontend` (Vercel auto-detects Vite; build
   command `npm run build`, output `dist`).
3. Add an Environment Variable:
   - `VITE_API_URL` = `https://visionflow-api.onrender.com` (no trailing slash)
4. Deploy. Vercel will give you a URL like `https://visionflow-xxxx.vercel.app`.

## 4. Close the loop on CORS
`app/main.py` already allows any `https://visionflow*.vercel.app` origin via
regex, plus `http://localhost:5173` for local dev, so most Vercel preview and
production URLs work without touching the code again. If your Vercel project
name isn't `visionflow`, add your exact domain via an env var on the Render
API service instead of editing code:
- `ALLOWED_ORIGINS` = `https://your-project-name.vercel.app`

## What the demo shows, out of the box
- **Predictions**: upload an image, pick resnet18 / mobilenet_v2 / yolov5n,
  see the async job go Queued -> Processing -> Completed with latency.
- **Metrics**: `StatsGrid` pulls live numbers from `GET /metrics`.
- **Architecture**: the `Architecture` section is a static diagram of the
  queue -> worker -> model pipeline — good to skim before your model server
  wakes up.

## If you'd rather not run a backend at all
An alternative, fully-Vercel-only demo is possible but would mean rewriting
`/predict` as a synchronous Vercel serverless function (no Redis, no worker,
no job polling) that loads one small ONNX model per request — a materially
different, simplified app rather than a deploy of this repo. Happy to build
that version instead if you'd prefer a single-platform demo over showing off
the real queue/worker architecture.