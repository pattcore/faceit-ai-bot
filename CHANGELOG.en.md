# What's New

**[Русская версия](CHANGELOG.md)**

## Version 0.5.1 — February 22, 2026

- Rebranding: migration from pattmsc to pattcore throughout the project
- Updated versions in pyproject.toml, package.json and config
- Fixed Let's Encrypt certificate paths in nginx configuration
- Automated SSL certificate renewal via certbot webroot

## Version 0.5.0 — January 24, 2026

- Fixed API ↔ PostgreSQL connectivity in production (Steam callback no longer returns 500).

## Version 0.4.9 — January 5, 2026

Release focused on production availability, secure authentication flows, and admin ergonomics.

### 🎉 Highlights

- 🔐 **CAPTCHA / login / registration fixes**  
  Restored working CAPTCHA validation and authentication flows.
- 📊 **Metrics & monitoring**  
  Prometheus metrics are available and verified in production: `/api/metrics`, with an easy entry point via `/metrics`.
- 🛡️ **Rate limit admin panel**  
  Restored access to `/api/admin/rate-limit/*` and UI, confirmed Redis status as connected.
- 🧩 **Production nginx (container) config**  
  Removed overly strict blocks that caused `403` for `/metrics` and admin endpoints.

### 🛠 Under the Hood

- Stabilized environment configuration (DB/Redis) and deployment setup.
- Improved observability: HTTP metrics, API error counters, DB pool metrics.

---

## Version 0.4.8 — December 14, 2025

Release focused on production stability and reliable auto‑startup after server reboots.

### 🎉 Highlights

- 🚀 **Reliable auto‑startup via systemd**  
  Introduced a single `faceit-api.service` systemd unit that brings up the entire Docker stack (`nginx`, `api`, `web`, `db`, `redis`, `celery`, bots). Removed legacy conflicting units and the system nginx service that was competing with the containerized nginx.
- 🐍 **Safe database initialization**  
  The `scripts/init_db.py` script now waits for Postgres to become available before creating tables. This eliminates random startup crashes when the DB container is still initializing.
- ⚙️ **Stable Celery worker/beat/flower startup**  
  Fixed Celery commands in `docker-compose.prod.yml` so that the worker no longer fails with CLI argument parsing errors and health checks pass consistently.
- 🧹 **Cleaner docker-compose output**  
  Removed the obsolete top‑level `version` key and added safe defaults for environment variables (`GROQ_API_KEY`, `NEXT_PUBLIC_SMARTCAPTCHA_SITE_KEY`) to avoid noisy Docker Compose WARN messages.

### 🛠 Under the Hood

- Production nginx configuration fixes.
- Minor improvements in backend typings and middleware.
- Updated README/CHANGELOG to reflect the 0.4.8 release.

---

## Version 0.4.6 — November 22, 2025

Small but important release focused on the ML pipeline and release infrastructure.

### 🎉 Highlights in 0.4.6

- 📦 **New web assets archive**  
  Automatic Next.js frontend build and publication of `faceit-ai-bot-web-assets-<version>.tar.gz` in GitHub Releases.
- 🧩 **Browser extension package**  
  The extension continues to be built automatically as a ZIP archive for Chrome/Edge installation.
- 🐳 **Docker package for server deployment**  
  Ready-to-use `faceit-ai-bot-docker-<version>.tar.gz` archive with `docker-compose.yml`, sample `.env` and README for quick startup.

### 🧠 ML / Infrastructure

- Infrastructure prepared for the ML pipeline for CS2 demo analysis:
  - `scripts/fetch_pro_demos.py` — collecting metadata of pro demos,
  - `scripts/download_pro_demos.py` — downloading demo files,
  - `scripts/extract_pro_demo_features.py` — extracting features from demos,
  - `scripts/export_demo_coach_dataset.py` — exporting a training dataset for the ML model.
- Pinned `demoparser2==0.40.2` in `requirements.txt` so that CI and GitHub Actions work reliably with ML scripts.

---

## Version 0.2.2 — November 9, 2025

Big update! Everything now works automatically and looks beautiful.

### 🎉 Highlights in 0.2.2

**Automatic Releases**  
Now when you create a tag, GitHub automatically builds extensions, Docker images, and publishes everything in a release. No more manual work!

**Extensions for All Browsers**  
Added automatic builds for Chrome, Firefox, Edge, and Opera. Just download and install.

**Docker Images**  
API and web version are now published to GitHub Container Registry. Can be quickly deployed on any server.

**Beautiful Project Page**  
Created a modern GitHub Pages with gradients and convenient download links.

**Testing Scripts**  
Added test-sites.ps1 for Windows and test-sites.sh for Linux. Run it and see what works and what doesn't.

### 📦 Downloads Available

**Extensions:**
- Chrome / Edge / Opera — ZIP archive
- Firefox — XPI file

**Docker:**
- API server — `ghcr.io/pat1one/faceit-ai-bot/api:v0.2.2`
- Web version — `ghcr.io/pat1one/faceit-ai-bot/web:v0.2.2`
- Ready package — `faceit-ai-bot-docker-v0.2.2.tar.gz`

### 🛠️ Under the Hood

- Configured webpack for extension builds
- Added GitHub Actions for automation
- Optimized Dockerfile — now builds faster
- Fixed healthcheck in containers
- Disabled ESLint during Docker build (speedup)

### 📝 Documentation

Updated README — added badges and made it clearer.  
Wrote DOWNLOAD.md — step-by-step instructions for all platforms.  
Created TEST_SCRIPTS.md — how to verify everything works.

### 🎨 Design

GitHub Pages now looks modern:
- Gradients and smooth transitions
- Responsive layout for mobile
- Convenient download buttons

### 🔧 Fixes

- Webpack now correctly copies files
- Simplified web version build — fewer errors
- Removed unnecessary mentions from texts

---

## Version 0.2.0

First working version with all core functionality.
