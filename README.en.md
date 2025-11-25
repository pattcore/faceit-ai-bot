# 🎮 Faceit AI Bot

<div align="center">

![Faceit AI Bot](https://img.shields.io/badge/Faceit_AI_Bot-v0.4.6-2E9EF7?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
[![License](https://img.shields.io/badge/License-Source--available-blue?style=for-the-badge)](LICENSE)
[![2028 License](https://img.shields.io/badge/2028_License-AGPL--3.0-orange?style=for-the-badge)](LICENSE)

**CS2 Player Analysis and Teammate Finder for Faceit Platform**

[🚀 Demo](https://pattmsc.online) • [📚 Documentation](https://pat1one.github.io/faceit-ai-bot/) • [📦 Release v0.4.6](https://github.com/pat1one/faceit-ai-bot/releases/tag/v0.4.6) • [🐛 Bug Reports](https://github.com/pat1one/faceit-ai-bot/issues)

**⬇️ Downloads (v0.4.6):**

- 🧩 `faceit-ai-bot-extension-v0.4.6.zip` — browser extension for Chrome/Edge,
- 🌐 `faceit-ai-bot-web-assets-v0.4.6.tar.gz` — prebuilt Next.js web assets,
- 🐳 `faceit-ai-bot-docker-v0.4.6.tar.gz` — Docker package with `docker-compose.yml` and sample `.env`.

All files are available in the **Assets** section of the v0.4.6 GitHub Release page.

**[Русская версия](README.md)**

</div>

---

## 📋 Description

A tool for analyzing CS2 player statistics on the Faceit platform. Helps find teammates, analyze demos, and improve gameplay through detailed statistics and personalized recommendations.

### ✨ Key Features

- 🤖 **AI-powered player analysis** — detailed statistics with human-like recommendations
- 🧠 **Groq-powered insights** — advanced analysis of gameplay patterns
- 📊 **Faceit API integration** — real-time match and player data
- �️ **PostgreSQL analytics storage** — history of player stats and reports
- �📈 **Demo file analysis** — breakdown of key rounds and situations in CS2 demos
- 👥 **Teammate search** — smart matching by rank, roles, languages and playstyle
- 💡 **Personalized training plans** — daily/weekly routines for faster improvement
- 📊 **Historical analytics** — track your progress and performance dynamics
- 🔮 **Match predictions** — win probability estimation based on stats
- 📱 **PWA support** — install as a mobile app on any device
- 🔒 **HTTPS security** — SSL protected connection
- ⚡ **High performance** — optimized VPS hosting with caching

---

## 🛠️ Technology Stack

### Backend

✅ **AI and data technologies:**
![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=ai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge)
![Languages](https://img.shields.io/badge/Languages-ru%20%7C%20en-6B21A8?style=for-the-badge)

**AI stack:**
- Unified `GroqService` with three providers:
  - local LLM via OpenAI-compatible endpoint (e.g. Ollama + qwen:0.5b),
  - OpenRouter (API key, model configured via settings),
  - native Groq API.
- AI is used for player analysis, detailed demo review and teammate compatibility ranking.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

### Frontend

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

### DevOps & Tools

![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)

---

## 🚀 How to Use

### 🌐 Web Version (Recommended)

✅ **The site is live and running in production!**

🌍 **Main site:** [pattmsc.online](https://pattmsc.online)
📚 **Documentation:** [GitHub Pages](https://pat1one.github.io/faceit-ai-bot/)

**Available features:**
- 🎯 CS2 player analysis by nickname
- 📊 Detailed statistics (K/D, win rate, headshot %)
- 📤 Demo upload and AI-powered demo analysis
- 👥 Teammate search with AI‑enhanced compatibility
- 🤖 Personalized recommendations and training plans
- ⚡ Fast performance with Redis caching
- 🔒 HTTPS and production deployment on VPS
 - 🔐 CAPTCHA protection for login, registration and payment creation (Cloudflare Turnstile + Yandex SmartCaptcha for Russian users)

---

### 🧩 Browser Extension

**Status:** Basic version available (manual install via Chrome/Edge)

Current extension capabilities:
- 🎯 Quickly open Faceit AI Bot from any page in the browser
- 👤 Trigger player analysis directly from Faceit player profile pages
- 🎮 Jump from Steam Community profiles to the Faceit AI Bot site

#### Manual Browser Extension Installation (Chrome/Edge)

1. Open the v0.4.6 release on GitHub (https://github.com/pat1one/faceit-ai-bot/releases/tag/v0.4.6) and download the extension archive from the **Assets** section, then unpack it (or download the whole repository as a ZIP).
2. Open `chrome://extensions` (for Chrome) or `edge://extensions` (for Microsoft Edge).
3. Enable **Developer mode**.
4. Click **"Load unpacked"** and select the `extension` folder inside the `faceit-ai-bot` project.
5. Make sure the **Faceit AI Bot Assistant** extension is enabled and pin its icon if you want quick access.
6. Log in on [pattmsc.online](https://pattmsc.online), then open the extension popup — it uses the same httpOnly session as the site.

Follow updates on [GitHub](https://github.com/pat1one/faceit-ai-bot)

---

### 📱 Mobile Application

**Status:** Planned

PWA application will be available after site deployment.

**Features:**
- 📱 Works as native application
- 🚀 Quick launch from home screen
- 📴 Partial offline functionality

---

### 🤖 Bots & Integrations

- 📢 Telegram bot for notifications and quick analysis requests (experimental, see docs for details).
- 🎧 Discord bot used as a demo of server integration and notifications.

> Disclaimer: Discord is blocked in some regions (including Russia), so you use it at your own risk. This integration is shown for educational/demo purposes only.

---

### 💻 Local Installation (For Developers)

<details>
<summary>Click to expand instructions</summary>

**Requirements:**
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- Git

**Installation:**

```bash
# Clone the repository
git clone https://github.com/pat1one/faceit-ai-bot.git
cd faceit-ai-bot

# Copy .env file
cp .env.example .env

# Fill in API keys in .env
# FACEIT_API_KEY=your_key

# Run via Docker (recommended)
docker-compose up -d

# Or run locally
# Backend
cd src/server
pip install -r requirements.txt
python main.py

# Frontend (in new terminal)
cd ../..
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

</details>

---

## 📚 Documentation

Detailed documentation for developers and contributors is available in the `/docs` folder:

- 📚 [Overview & quick start](./docs/index.md)
- 🧱 [Architecture](./docs/architecture.md)
- 🧠 [ML training pipeline](./docs/ml-training.md)
- 🔌 [API Documentation](./docs/api/README.md)
- 🤝 [Contribution Guide](./CONTRIBUTING.md)

---

## 🗺️ Roadmap

<details>
<summary><b>📍 Current Version: v0.4.6</b></summary>

### ✅ Implemented in v0.4.1

- [x] Faceit API integration
- [x] Smart analysis with Groq AI
- [x] Personalized recommendations
- [x] Redis caching
- [x] Rate limiting
- [x] Docker Compose
- [x] CI/CD via GitHub Actions
- [x] Unit tests
- [x] 🚀 Production deployment on VPS
- [x] 🌐 HTTPS with Let's Encrypt
- [x] 📱 Responsive UI with Tailwind CSS
- [x] 📤 Demo upload and analysis
- [x] 👥 Teammate search
- [x] 🎨 Modern UI with animations
- [x] 🔧 Nginx reverse proxy
- [x] 📊 Improved analytics
- [x] 🔄 Automatic deploy pipeline

### 🧩 Browser extension (status)

- ✅ **Basic browser extension available** (Chrome/Edge, manual install from `extension` folder)
- 🚧 Store publishing (Chrome Web Store / other stores) and UX polish are planned for v0.5.0

</details>

### 🚧 v0.5 — ML model on pro demos

**Focus:** high‑quality ML analysis of gameplay relative to pro level.

- [ ] 📂 Dataset of top Faceit players (1000+ pro demos)
- [ ] 🧠 ML model producing:
  - positioning / decision making / utility / economy scores
  - overall pro‑likeness score (0–100)
- [ ] 📑 Report with the top 5 differences from pro players and concrete round examples

### 🚧 v0.6 — Browser extension

**Focus:** frictionless entry point from Faceit.

- [ ] 🧩 Updated Chrome/Edge extension
- [ ] 🔘 One button on Faceit profile → full AI analysis
- [ ] 🔗 Deep link to the web UI with detailed report and visualizations (heatmaps, comparisons)

### 🚧 v0.7 — Monetization

**Focus:** first paid tiers around ML analytics.**

- [ ] 💳 Payment integration
- [ ] 🎯 Plans:
  - Free — 1 demo per month, basic report
  - Pro — unlimited demos, full ML analysis and pro comparison
  - Team — team analysis, teammate comparison, opponent analysis

### 🎯 v1.0 — Stable product

**Focus:** stable ML platform with real paying customers.**

- [ ] Reliable ML pipeline (retraining, quality metrics)
- [ ] Performance optimization and demo analysis queues
- [ ] Polished UX (heatmaps, comparisons, clear reports)
- [ ] Iterations based on feedback from active users

> Ideas like mobile apps, other games, coach marketplace and heavy social features are **post‑1.0** and will be considered only after product‑market fit and stable revenue.

**Want to suggest a feature?** [Create an issue](https://github.com/pat1one/faceit-ai-bot/issues/new) with the `feature-request` tag

---

## 🤝 Contributing

We welcome contributions to the project!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Rules

- Follow PEP 8 for Python code
- Use ESLint/Prettier for TypeScript
- Write tests for new features
- Update documentation

---

## 📊 Project Statistics

![GitHub Stars](https://img.shields.io/github/stars/pat1one/faceit-ai-bot?style=social)
![GitHub Forks](https://img.shields.io/github/forks/pat1one/faceit-ai-bot?style=social)
![GitHub Issues](https://img.shields.io/github/issues/pat1one/faceit-ai-bot)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/pat1one/faceit-ai-bot)

---

## 📄 License

This project is distributed under a custom **source-available** license.
See the [LICENSE](LICENSE) file for full terms and conditions.

---

## 💼 Contacts

<div align="center">

[![Telegram](https://img.shields.io/badge/Business-Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/prdrow)
[![Email](https://img.shields.io/badge/Advertising-Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:drow.battle.2025@gmail.com)
[![Taplink](https://img.shields.io/badge/All_Links-Taplink-00D9FF?style=for-the-badge&logo=linktree&logoColor=white)](https://taplink.cc/mscpat)
[![Twitch](https://img.shields.io/badge/Stream-Twitch-9146FF?style=for-the-badge&logo=twitch&logoColor=white)](https://www.twitch.tv/pattmsc)
[![GitHub](https://img.shields.io/badge/Code-GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/pat1one)

</div>

---

---

<div align="center">

**⭐ If you like the project, give it a star! ⭐**

</div>
