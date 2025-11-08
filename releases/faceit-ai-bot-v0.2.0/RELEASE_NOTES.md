# Faceit AI Bot v0.2.0

## Что в релизе

### Расширение для браузера

- faceit-ai-bot-extension-v0.2.0.zip - архив с расширением
- Устанавливается через chrome://extensions в режиме разработчика

### Docker

- Все файлы для запуска через Docker
- docker-compose.yml для быстрого старта
- Скрипты деплоя

### Документация

- README.md
- Пример конфига (.env.example)

## Как установить

### Установка расширения

1. Распакуйте faceit-ai-bot-extension-v0.2.0.zip
2. Откройте chrome://extensions
3. Включите режим разработчика
4. Загрузите распакованное расширение
5. Выберите папку с файлами

### Установка через Docker

```bash
cd docker
cp .env.example .env
# Поправьте настройки в .env
docker-compose up -d
```

### Через скрипты

```bash
cd scripts
chmod +x *.sh
./deploy.sh
```

## Что будет доступно

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>
- API Docs: <http://localhost:8000/docs>
- PostgreSQL: localhost:5432

## Стек

- Frontend: Next.js 15, React 19, TypeScript
- Backend: FastAPI, Python 3.9+
- БД: PostgreSQL 16
- Расширение: Webpack, Babel
- Деплой: Docker, Docker Compose

## Изменения

- Версия 0.2.0
- Оптимизация работы
- Фиксы багов

---
08.11.2025
