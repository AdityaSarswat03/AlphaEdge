# Deployment Guide

## Local Development

```bash
# Install
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# API
uvicorn alphaedge.api.main:app --reload --port 8000

# Dashboard
streamlit run src/dashboard/app.py
```

---

## Service Setup

### Firebase (Database)

1. Create a project at [Firebase Console](https://console.firebase.google.com/)
2. Enable **Firestore Database** in **Native mode**
3. Go to Project Settings → Service Accounts → Generate new private key
4. Save the JSON as `config/firebase-service-account.json` (git-ignored)
5. Set in `.env`:
   ```
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_CREDENTIALS_PATH=config/firebase-service-account.json
   ```

### Clerk (Authentication)

1. Sign up at [clerk.com](https://clerk.com) and create an application
2. Choose sign-in methods (email, Google, GitHub, etc.)
3. Copy keys into `.env`:
   ```
   CLERK_PUBLISHABLE_KEY=pk_live_…
   CLERK_SECRET_KEY=sk_live_…
   CLERK_DOMAIN=your-app.clerk.accounts.dev
   ENABLE_CLERK_AUTH=true
   ```
4. In Clerk Dashboard → JWT Templates → ensure RS256 is used
5. Add your production domain to Clerk's allowed origins

### Cloudflare (DNS & CDN)

1. Add your domain to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Update nameservers at your registrar to Cloudflare's
3. Create an API token: Zone → DNS → Edit
4. Set in `.env`:
   ```
   CLOUDFLARE_API_TOKEN=your-token
   CLOUDFLARE_ZONE_ID=your-zone-id
   DOMAIN_NAME=alphaedge.ai
   ```
5. Or use the helper to auto-configure DNS:
   ```python
   from alphaedge.utils.cloudflare import setup_alphaedge_dns
   setup_alphaedge_dns("YOUR_SERVER_IP")
   ```

### GitHub (Version Control & CI/CD)

1. Push to `https://github.com/adityas/AlphaEdge`
2. CI runs automatically on push to `main` / `develop` (see `.github/workflows/ci.yml`)
3. Set repository secrets for production:
   - `FIREBASE_CREDENTIALS_JSON`
   - `CLERK_SECRET_KEY`
   - `CLOUDFLARE_API_TOKEN`

---

## Docker

```bash
# Build & run all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

**Services:**
| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI server |
| `dashboard` | 8501 | Streamlit UI |
| `redis` | 6379 | Cache (optional) |

---

## Environment Variables

See `.env.example` for all options. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `FIREBASE_PROJECT_ID` | | Firebase project ID |
| `FIREBASE_CREDENTIALS_PATH` | | Path to service-account JSON |
| `CLERK_SECRET_KEY` | | Clerk backend secret key |
| `CLERK_DOMAIN` | | Clerk frontend domain |
| `ENABLE_CLERK_AUTH` | false | Enable JWT verification |
| `CLOUDFLARE_API_TOKEN` | | Cloudflare API token |
| `CLOUDFLARE_ZONE_ID` | | Cloudflare zone ID |
| `DOMAIN_NAME` | alphaedge.ai | Your domain |
| `ENABLE_REDIS_CACHE` | false | Enable Redis caching |

---

## Production Checklist

1. Set `DEBUG=false` and `APP_ENV=production` in `.env`
2. Configure Firebase Firestore with proper security rules
3. Enable Clerk auth (`ENABLE_CLERK_AUTH=true`)
4. Point DNS via Cloudflare (proxied, SSL Full Strict)
5. Use `gunicorn` with `uvicorn` workers:
   ```bash
   gunicorn alphaedge.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
6. Enable Redis for caching
7. Schedule `scripts/update_data.py` via cron / Cloud Scheduler
8. Retrain models periodically with `scripts/train_models.py`
9. Set up Cloudflare Page Rules for cache headers
10. Enable Cloudflare WAF for API protection

---

## Monitoring

- **Health endpoint:** `GET /health` — returns Firebase + auth status
- **Logs:** `logs/alphaedge.log` (auto-rotated at 10 MB, 7 days retention)
- **Firebase:** Use Firebase Console → Firestore → Usage tab
- **Cloudflare:** Analytics dashboard for traffic, threats, cache hit ratio
- **GitHub Actions:** CI status badges in README
