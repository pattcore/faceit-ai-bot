# 🎮 Faceit AI Bot

<div align="center">

![Faceit AI Bot](https://img.shields.io/badge/Faceit_AI_Bot-v0.4.0-2E9EF7?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**CS2 Player Analysis and Teammate Finder for Faceit Platform**

[🚀 Demo](https://pattmsc.online) • [📚 Documentation](https://docs.pattmsc.online) • [📦 Release v0.4.0](https://github.com/pat1one/faceit-ai-bot/releases/tag/v0.4.0) • [🐛 Bug Reports](https://github.com/pat1one/faceit-ai-bot/issues)

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
📚 **Documentation:** [docs.pattmsc.online](https://docs.pattmsc.online)

**Available features:**
- 🎯 CS2 player analysis by nickname
- 📊 Detailed statistics (K/D, win rate, headshot %)
- 📤 Demo upload and AI-powered demo analysis
- 👥 Teammate search with AI‑enhanced compatibility
- 🤖 Personalized recommendations and training plans
- ⚡ Fast performance with Redis caching
- 🔒 HTTPS and production deployment on VPS

---

### 🧩 Browser Extension

**Status:** In Development

The extension will allow:
- 🎯 Analyze players directly on Faceit
- ⚡ Get statistics with one click
- 📊 View teammate recommendations

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

- 📖 [User Guide](./docs/USER_GUIDE.md)
- 🔧 [Developer Guide](./docs/DEVELOPER_GUIDE.md)
- 🔌 [API Documentation](./docs/API.md)
- 🤝 [Contribution Guide](./CONTRIBUTING.md)

---

## 🗺️ Roadmap

<details>
<summary><b>📍 Current Version: v0.4.0</b></summary>

### ✅ Implemented in v0.4.0

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

</details>

### 🚧 v0.5.0 - In Development (Q1 2026)

**Focus:** deeper analytics, Steam integration and progression systems.

- [ ] 📊 **Advanced analytics**
  - Match history with rich charts and filters
  - Comparison with other players and peer groups
  - Detailed per-map and per-role statistics
- [ ] 🎮 **Steam integration**
  - Import demos directly from Steam
  - Profile synchronization between platforms
- [ ] 🏆 **Achievement system**
  - Clear progress tracking and goals
  - Rewards for skill improvements
- [ ] 🧩 **Browser extension**
  - Chrome/Firefox extension
  - One-click analysis directly on Faceit

### 🔮 v0.5.0 - Planned (Q2 2026)

**Focus:** social features, team tools and mobile experience.

- [ ] 💬 **Discord bot**
  - Analysis commands
  - Match notifications
  - Teammate search inside Discord
- [ ] 👥 **Team analytics**
  - Team synergy and role analysis
  - Roster recommendations
  - Tournament statistics
- [ ] 📱 **Native mobile app**
  - iOS/Android app
  - Push notifications
  - Offline mode

### 🌟 v0.5.0+ - Future (Q3–Q4 2026)

**Focus:** platform expansion, coaching ecosystem and advanced AI.

- [ ] 🎯 **Support for other games**
  - Dota 2
  - Valorant
  - League of Legends
- [ ] 🎓 **Coach marketplace**
  - Find coaches
  - Session booking
  - Review system
- [ ] 📺 **Stream integration**
  - Twitch/YouTube integration
  - Real-time stream analysis
  - Best moment clips
- [ ] 🤖 **Advanced AI**
  - Voice assistant
  - Match outcome prediction
  - Personal AI coach

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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
