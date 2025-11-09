# 🛠️ Development Guide

Руководство по разработке Faceit AI Bot v0.2.2

**[English version](DEVELOPMENT.en.md)**

## 📋 Требования

- **Node.js**: 18.x или выше
- **Python**: 3.9 или выше
- **Docker**: 20.10+ (опционально)
- **PostgreSQL**: 16+ (или через Docker)

## 🚀 Быстрый старт

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
git clone https://github.com/pat1one/faceit-ai-bot.git
cd faceit-ai-bot

# Установить Node.js зависимости
npm install

# Установить Python зависимости
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
# Создать .env файл
cp .env.example .env

# Отредактировать .env и установить:
# - SECRET_KEY (минимум 32 символа)
# - DATABASE_URL
# - API ключи для платежей (опционально)
```

### 3. Запуск

#### Через Docker (рекомендуется)

```bash
# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f
```

Доступно на:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Локально

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend
python main.py

# Terminal 3: Database (если не используете Docker)
# Запустите PostgreSQL локально
```

## 📁 Структура проекта

```text
faceit-ai-bot/
├── app/                    # Next.js 15 App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── src/
│   ├── components/        # React компоненты
│   ├── config/           # Конфигурация (API endpoints)
│   ├── server/           # FastAPI backend
│   │   ├── features/     # Модульные фичи
│   │   │   ├── demo_analyzer/
│   │   │   ├── payments/
│   │   │   ├── subscriptions/
│   │   │   └── teammates/
│   │   ├── models/       # Database models
│   │   ├── config/       # Settings
│   │   └── main.py       # FastAPI app
│   └── ai/              # AI/ML сервис
├── main.py              # Backend entry point
├── docker-compose.yml   # Docker orchestration
└── .env                # Environment variables
```

## 🔧 Основные команды

### NPM Scripts

```bash
# Development
npm run dev              # Запуск Next.js dev server
npm run build            # Production build
npm run start            # Production server

# Testing
npm run test             # Run tests
npm run type-check       # TypeScript проверка
npm run lint             # ESLint проверка

# Docker
npm run docker:build     # Build Docker images
npm run docker:up        # Start containers
npm run docker:down      # Stop containers
npm run docker:logs      # View logs
```

### Python Commands

```bash
# Testing
pytest tests/unit -v                    # Unit tests
pytest tests/integration -v             # Integration tests
pytest tests --cov=src/server          # With coverage

# Database migrations (когда будут добавлены)
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m ""   # Create migration
```

## 🧪 Тестирование

### Frontend Tests

```bash
npm run test
```

### Backend Tests

```bash
# Все тесты
pytest tests -v

# С coverage
pytest tests --cov=src/server --cov-report=html

# Только unit tests
pytest tests/unit -v
```

## 📝 Code Style

### TypeScript/React

- **Strict mode** включён
- **ESLint** для проверки кода
- **Prettier** для форматирования
- Используйте **TypeScript** типы везде

### Python

- **PEP 8** style guide
- **Type hints** обязательны
- **Docstrings** для всех публичных функций
- **Pydantic** для валидации данных

## 🔍 Debugging

### Frontend

```bash
# Next.js dev mode с подробными ошибками
npm run dev
```

### Backend

```bash
# FastAPI с auto-reload
uvicorn main:app --reload --log-level debug
```

### Docker

```bash
# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f web

# Войти в контейнер
docker-compose exec api bash
docker-compose exec web sh
```

## 🚢 Deployment

### Production Build

```bash
# Build all
npm run build:all

# Docker production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Обязательные для production:

```env
NODE_ENV=production
SECRET_KEY=<strong-secret-key-min-32-chars>
DATABASE_URL=postgresql://user:password@host:5432/db
```

## 📚 API Documentation

После запуска доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Создайте feature branch
2. Сделайте изменения
3. Напишите тесты
4. Проверьте линтеры: `npm run lint && npm run type-check`
5. Создайте Pull Request

## 🐛 Troubleshooting

### Port already in use

```bash
# Найти процесс на порту 3000
lsof -i :3000
# Убить процесс
kill -9 <PID>
```

### Docker issues

```bash
# Пересобрать без кеша
docker-compose build --no-cache

# Очистить всё
docker-compose down -v
docker system prune -a
```

### TypeScript errors

```bash
# Удалить кеш и пересобрать
rm -rf .next node_modules
npm install
npm run build
```

## 📞 Support

- 📧 Email: support@pattmsc.online
- 💬 GitHub Issues: [Bug Tracker](https://github.com/pat1one/faceit-ai-bot/issues)
- 📖 Docs: [README.md](README.md)

---

Сделано с ❤️ для CS2 комьюнити
