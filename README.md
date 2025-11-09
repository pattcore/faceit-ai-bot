# 🎮 Faceit AI Bot

<div align="center">

![Faceit AI Bot](https://img.shields.io/badge/Faceit_AI_Bot-v0.2.2-2E9EF7?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**AI-powered анализ игроков CS2 и поиск тиммейтов на платформе Faceit**

[🚀 Демо](https://pattmsc.online) • [📚 Документация](./docs) • [🐛 Баг-репорты](https://github.com/pat1one/faceit-ai-bot/issues)

</div>

---

## 📋 Описание

**Faceit AI Bot** — это мощный инструмент для анализа статистики игроков CS2 на платформе Faceit с использованием искусственного интеллекта. Проект объединяет современные технологии машинного обучения и веб-разработки для предоставления детального анализа игровой производительности.

### ✨ Основные возможности

- 🤖 **AI-анализ игроков** — GPT-4 анализирует статистику и дает персональные рекомендации
- 📊 **Интеграция с Faceit API** — получение актуальной статистики в реальном времени
- 📈 **Анализ демо-файлов** — детальный разбор игровых моментов
- 👥 **Поиск тиммейтов** — умный подбор напарников по стилю игры
- 💡 **Персональные планы тренировок** — AI создает индивидуальные программы улучшения
- 🔮 **Предсказание результатов** — прогнозирование исходов матчей
- 📱 **PWA поддержка** — установка как мобильное приложение

---

## 🛠️ Технологический стек

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)
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

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Установка

```fish
# Клонируйте репозиторий
git clone https://github.com/pat1one/faceit-ai-bot.git
cd faceit-ai-bot

# Скопируйте .env файл
cp .env.example .env

# Заполните API ключи в .env
# OPENAI_API_KEY=your_key
# FACEIT_API_KEY=your_key

# Запустите через Docker
docker-compose up -d

# Или запустите локально
# Backend
cd src/server
pip install -r requirements.txt
python main.py

# Frontend
cd ../..
npm install
npm run dev
```

### 📱 Установка PWA

**iOS:**
1. Откройте сайт в Safari
2. Нажмите "Поделиться" → "На экран Домой"

**Android:**
1. Откройте сайт в Chrome
2. Меню → "Установить приложение"

Подробнее: [PWA_GUIDE.md](./PWA_GUIDE.md)

---

## 📚 Документация

- [🔧 AI Integration Guide](./AI_INTEGRATION.md) — интеграция AI сервисов
- [🔑 API Keys Guide](./API_KEYS_GUIDE.md) — получение API ключей
- [⚙️ AI Setup](./AI_SETUP.md) — настройка AI компонентов
- [📱 PWA Guide](./PWA_GUIDE.md) — установка мобильного приложения
- [🎨 Icons Guide](./ICONS_GUIDE.md) — генерация иконок

---

## 🎯 Roadmap

### v0.3.0 (В разработке)
- [ ] Улучшенный AI анализ с контекстом истории
- [ ] Интеграция с Steam API
- [ ] Система достижений
- [ ] Расширенная аналитика команд

### v0.4.0 (Планируется)
- [ ] Мобильное приложение (React Native)
- [ ] Голосовой ассистент
- [ ] Интеграция с Discord
- [ ] Турнирная система

### Будущие планы
- [ ] Поддержка других игр (Dota 2, Valorant)
- [ ] Marketplace для тренеров
- [ ] Стриминг интеграция (Twitch, YouTube)

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
