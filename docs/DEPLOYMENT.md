# Deployment Guide

The platform is designed to be easily deployed to modern infrastructure.

1. **DNS** — Point `api.alphaedge.ai` and `app.alphaedge.ai` to your server via Cloudflare
2. **Auth** — Set `ENABLE_CLERK_AUTH=true` in production
3. **Security** — Change `SECRET_KEY` from the default (enforced in production)
4. **Database** — Firestore is serverless, no infra to manage
5. **CI/CD** — Push to `main` triggers GitHub Actions (lint → test → Docker build)
