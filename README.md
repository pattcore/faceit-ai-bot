# 🎮 Faceit AI Bot

<div align="center">

![Faceit AI Bot](https://img.shields.io/badge/Faceit_AI_Bot-v0.4.0-2E9EF7?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[![CI](https://github.com/pat1one/faceit-ai-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/pat1one/faceit-ai-bot/actions/workflows/ci.yml)
[![Deploy](https://github.com/pat1one/faceit-ai-bot/actions/workflows/deploy-to-vps.yml/badge.svg)](https://github.com/pat1one/faceit-ai-bot/actions/workflows/deploy-to-vps.yml)
[![Docs](https://github.com/pat1one/faceit-ai-bot/actions/workflows/deploy-docs.yml/badge.svg)](https://docs.pattmsc.online)
[![Site Status](https://img.shields.io/badge/Site-Online-brightgreen?style=for-the-badge)](https://pattmsc.online)
[![Documentation](https://img.shields.io/badge/Documentation-Available-blue?style=for-the-badge)](https://docs.pattmsc.online)
[![CodeQL](https://github.com/pat1one/faceit-ai-bot/actions/workflows/codeql.yml/badge.svg)](https://github.com/pat1one/faceit-ai-bot/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/pat1one/faceit-ai-bot/branch/main/graph/badge.svg)](https://codecov.io/gh/pat1one/faceit-ai-bot)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-brightgreen)](https://github.com/pat1one/faceit-ai-bot)
[![GitHub issues](https://img.shields.io/github/issues/pat1one/faceit-ai-bot)](https://github.com/pat1one/faceit-ai-bot/issues)
[![GitHub stars](https://img.shields.io/github/stars/pat1one/faceit-ai-bot)](https://github.com/pat1one/faceit-ai-bot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/pat1one/faceit-ai-bot)](https://github.com/pat1one/faceit-ai-bot/network)

**Анализ игроков CS2 и поиск тиммейтов на платформе Faceit**

✅ **Сайт активно работает: [pattmsc.online](https://pattmsc.online)**  
📚 **Документация доступна: [docs.pattmsc.online](https://docs.pattmsc.online)**

[🚀 Демо](https://pattmsc.online) • [📚 Документация](https://docs.pattmsc.online) • [📦 Релиз v0.4.0](https://github.com/pat1one/faceit-ai-bot/releases/tag/v0.4.0) • [🐛 Баг-репорты](https://github.com/pat1one/faceit-ai-bot/issues) • [💡 Идеи](https://github.com/pat1one/faceit-ai-bot/issues/new?template=feature_request.md)

**[English version](README.en.md)** | **[Contributing](CONTRIBUTING.md)** | **[Changelog](CHANGELOG.md)** | **[FAQ](FAQ.md)**

</div>

---

## 📋 Описание

✅ **Запущен и работает в продакшене!**

Инструмент для анализа статистики игроков CS2 на платформе Faceit. Помогает находить тиммейтов, анализировать демки и улучшать свою игру через детальную статистику и персональные рекомендации.

🌍 **Доступен онлайн:** [pattmsc.online](https://pattmsc.online)

### ✨ Основные возможности

🚀 **Все функции доступны на работающем сайте:**

- 🤖 **AI анализ игроков** — умная обработка статистики с персональными рекомендациями
- 🧠 **Groq powered insights** — продвинутый анализ игровых паттернов
- 📊 **Интеграция с Faceit API** — актуальные данные матчей и игроков в реальном времени
- 🗄️ **База данных PostgreSQL** — хранение истории аналитики и статистики
- 📈 **Анализ демо-файлов** — детальный разбор игровых моментов и ключевых ситуаций
- 👥 **Поиск тиммейтов** — умный подбор напарников по стилю игры и совместимости
- 💡 **Персональные планы тренировок** — индивидуальные программы улучшения навыков
- 📊 **Историческая аналитика** — отслеживание прогресса и динамики показателей
- 🔮 **Прогнозы матчей** — анализ шансов на победу на основе статистики
- 📱 **PWA поддержка** — установка как мобильное приложение на любое устройство
- 🔒 **HTTPS защита** — безопасное соединение с SSL сертификатом
- ⚡ **Высокая производительность** — оптимизированный хостинг на VPS

---

## 🛠️ Технологический стек

### Backend

✅ **AI и Data технологии:**
![Groq](https://img.shields.io/badge/Groq-FFA500?style=for-the-badge&logo=groq&logoColor=black)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)

**AI-стек приложения:**
- Единый сервис `GroqService` с поддержкой трёх провайдеров:
  - локальный LLM через OpenAI-совместимый endpoint (например, Ollama + qwen:0.5b),
  - OpenRouter (по API-ключу, модель настраивается в конфиге),
  - нативный Groq API.
- AI используется для анализа игроков, детального разбора демок и подбора тиммейтов по совместимости.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

### Frontend

![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

### DevOps & Tools

✅ **Продакшн развертывание:**
- 🌐 **VPS хостинг** на Ubuntu 24.04
- 🔒 **Let's Encrypt SSL** сертификат
- 🚀 **Nginx reverse proxy** с оптимизацией
- 🐳 **Docker контейнеры** для всех сервисов
- 🗄️ **PostgreSQL база данных** для аналитики
- 🔄 **Redis кэширование** для производительности
- 🤖 **Groq AI интеграция** для анализа
- 🔄 **CI/CD автоматизация** через GitHub Actions

![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)

---

## 🚀 Как использовать

### 🌐 Веб-версия (Рекомендуется)

✅ **Сайт успешно запущен и работает!**

🌍 **Основной сайт:** [pattmsc.online](https://pattmsc.online)
📚 **Документация:** [docs.pattmsc.online](https://docs.pattmsc.online) (субдомен)

**Возможности:**
- 🎯 Анализ игроков CS2 по никнейму
- 📊 Детальная статистика (K/D, Win Rate, Headshots)
- 📤 Загрузка и анализ демо-файлов
- 👥 Поиск тиммейтов
- 🤖 Персональные рекомендации
- ⚡ Быстрая работа с кэшированием
- 🔒 Безопасное соединение (HTTPS)
- 📱 Адаптивный дизайн для всех устройств

---

### 🧩 Браузерное расширение

**Статус:** В разработке

Расширение позволит:
- 🎯 Анализировать игроков прямо на Faceit
- ⚡ Получать статистику в один клик
- 📊 Видеть рекомендации по тиммейтам

Следите за обновлениями на [GitHub](https://github.com/pat1one/faceit-ai-bot)

---

### 📱 Мобильное приложение

**Статус:** Запланировано

PWA приложение будет доступно после деплоя сайта.

**Возможности:**
- 📱 Работа как нативное приложение
- 🚀 Быстрый запуск с главного экрана
- 📴 Частичная работа офлайн

---

### 💻 Локальная установка (Для разработчиков)

<details>
<summary>Нажмите чтобы развернуть инструкцию</summary>

**Требования:**
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (опционально)
- Git

**Установка:**

```bash
# Клонируйте репозиторий
git clone https://github.com/pat1one/faceit-ai-bot.git
cd faceit-ai-bot

# Скопируйте .env файл
cp .env.example .env

# Заполните API ключи в .env
# FACEIT_API_KEY=your_key

# Запустите через Docker (рекомендуется)
docker-compose up -d

# Или запустите локально
# Backend
cd src/server
pip install -r requirements.txt
python main.py

# Frontend (в новом терминале)
cd ../..
npm install
npm run dev
```

**Доступ:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

</details>

---

## 📚 Документация

Для разработчиков и контрибьюторов доступна подробная документация в папке `/docs`:

- 📖 [Руководство пользователя](./docs/USER_GUIDE.md)
- 🔧 [Руководство разработчика](./docs/DEVELOPER_GUIDE.md)
- 🔌 [API документация](./docs/API.md)
- 🤝 [Гайд по контрибуции](./CONTRIBUTING.md)

---

## 🗺️ Roadmap

<details>
<summary><b>📍 Текущая версия: v0.4.0</b></summary>

### ✅ Реализовано в v0.4.0

- [x] Интеграция с Faceit API
- [x] Умный анализ с Groq AI
- [x] Персональные рекомендации
- [x] Redis кэширование
- [x] Rate limiting
- [x] Docker Compose
- [x] CI/CD через GitHub Actions
- [x] Unit тесты
- [x] **🚀 Продакшн деплой на VPS**
- [x] **🌐 HTTPS с Let's Encrypt**
- [x] **📱 Адаптивный дизайн с Tailwind CSS**
- [x] **📤 Загрузка демо-файлов**
- [x] **👥 Поиск тиммейтов**
- [x] **🎨 Современный UI с анимациями**
- [x] **🔧 Nginx reverse proxy**
- [x] **📊 Улучшенная аналитика**
- [x] **🔄 Автоматический деплой**

</details>

### 🚧 v0.5.0 - В разработке (Q1 2026)

**Основные фичи:**
- [ ] 📊 **Расширенная аналитика**
  - История матчей с графиками
  - Сравнение с другими игроками
  - Детальная статистика по картам
- [ ] 🎮 **Интеграция с Steam**
  - Импорт демок из Steam
  - Синхронизация профиля
- [ ] 🏆 **Система достижений**
  - Прогресс и цели
  - Награды за улучшения
- [ ] 🧩 **Браузерное расширение**
  - Chrome/Firefox extension
  - Анализ прямо на Faceit

### 🔮 v0.5.0 - Планируется (Q2 2026)

**Социальные функции:**
- [ ] 💬 **Discord бот**
  - Команды для анализа
  - Уведомления о матчах
  - Поиск тиммейтов в Discord
- [ ] 👥 **Командная аналитика**
  - Анализ синергии команды
  - Рекомендации по составу
  - Турнирная статистика
- [ ] 📱 **Нативное мобильное приложение**
  - iOS/Android app
  - Push-уведомления
  - Офлайн режим

### 🌟 v0.5.0+ - Будущее (Q3-Q4 2026)

**Расширение платформы:**
- [ ] 🎯 **Поддержка других игр**
  - Dota 2
  - Valorant
  - League of Legends
- [ ] 🎓 **Marketplace тренеров**
  - Поиск тренеров
  - Бронирование сессий
  - Система отзывов
- [ ] 📺 **Интеграция со стримами**
  - Twitch/YouTube интеграция
  - Анализ стримов в реальном времени
  - Клипы с лучшими моментами
- [ ] 🤖 **Продвинутый AI**
  - Голосовой ассистент
  - Предсказание исходов матчей
  - Персональный AI-тренер

**Хотите предложить фичу?** [Создайте issue](https://github.com/pat1one/faceit-ai-bot/issues/new) с тегом `feature-request`

---

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта!

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

### Правила разработки

- Следуйте PEP 8 для Python кода
- Используйте ESLint/Prettier для TypeScript
- Пишите тесты для новых функций
- Обновляйте документацию

---

## 📊 Статистика проекта

![GitHub Stars](https://img.shields.io/github/stars/pat1one/faceit-ai-bot?style=social)
![GitHub Forks](https://img.shields.io/github/forks/pat1one/faceit-ai-bot?style=social)
![GitHub Issues](https://img.shields.io/github/issues/pat1one/faceit-ai-bot)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/pat1one/faceit-ai-bot)

---

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

---

## 💼 Контакты

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

**⭐ Если проект понравился, поставьте звезду! ⭐**

</div>
