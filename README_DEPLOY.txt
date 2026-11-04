HOUSEBOOK KENYA — PAYHERO DEPLOYMENT STARTER

WHAT IS THIS?
This is a complete single Flask web app: FRONTEND (HTML/CSS pages and forms) + BACKEND (Python routes, booking logic, SQLite, PayHero STK). It is not a separate React frontend. Deploy as one web service.

FILES
app.py — website and backend
requirements.txt — Python dependencies
render.yaml — Render Blueprint
README_DEPLOY.txt — these instructions

IMPORTANT
This is a starter/demo. It does not yet include customer/owner login, admin dashboard, listing moderation, CSRF protection, or hardened PayHero callback verification. Do not call listings verified. Secure and test thoroughly before accepting real customer payments. Never put API secrets in GitHub or app.py.

PAYHERO VARIABLES (keep values private)
PAYHERO_API_USERNAME = PayHero API username
PAYHERO_API_PASSWORD = PayHero API password/token
PAYHERO_CHANNEL_ID = numeric PayHero channel ID
PUBLIC_BASE_URL = public HTTPS URL, no trailing slash
SECRET_KEY = long random secret
DATABASE_PATH = persistent database path
Callback URL sent by app: https://YOUR-DOMAIN/payhero/callback

DEPLOY WITH RENDER (recommended if using render.yaml)
1. Download and unzip this ZIP.
2. Create a GitHub repository. Upload app.py, requirements.txt, render.yaml, README_DEPLOY.txt into the repository ROOT (not the ZIP alone).
3. Render dashboard → New → Blueprint → connect that GitHub repository. Render reads render.yaml.
4. Open Render service → Environment. Set PayHero variables above, SECRET_KEY, PUBLIC_BASE_URL (your Render URL), and DATABASE_PATH=/var/data/housebook.db.
5. Save/redeploy. Wait for Live. Open YOUR-RENDER-URL/health; expect status ok.
6. Open the main URL, add a sample property, then test an STK payment with a small amount.
Note: Render persistent disks require a paid web service. The included Blueprint mounts disk at /var/data. SQLite must be on that disk.

DEPLOY WITH RAILWAY
1. Upload those same four files to GitHub repository ROOT.
2. Railway → New Project → Deploy from GitHub Repo → select repository.
3. If a start command is requested, use: gunicorn app:app
4. Add a Volume to the app service and set its mount path to /data.
5. Railway service → Variables: set PAYHERO_API_USERNAME, PAYHERO_API_PASSWORD, PAYHERO_CHANNEL_ID, SECRET_KEY, PUBLIC_BASE_URL (Railway public HTTPS domain), DATABASE_PATH=/data/housebook.db.
6. Settings/Networking → Generate Domain. Redeploy after variables are set.
7. Visit YOUR-RAILWAY-DOMAIN/health and test the website and STK.

DATA WARNING
Without persistent disk/volume, SQLite data can disappear on redeploy/restart. Render: /var/data/housebook.db. Railway: /data/housebook.db.

TROUBLESHOOTING
- Build issue: requirements.txt must be in repository root.
- Start command: gunicorn app:app
- PayHero not configured: verify all environment variables and redeploy.
- STK failure: verify API credentials, channel ID, phone number and service logs.
- /health is only a health test; homepage is the domain root /.
