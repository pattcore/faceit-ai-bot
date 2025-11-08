<div align="center">

# 🎮 Faceit AI Bot

### Умный анализ статистики и поиск тиммейтов для CS2

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/next.js-15-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

[🌐 Демо](https://pattmsc.online) • [📚 Документация](https://api.pattmsc.online/docs) • [⬇️ Скачать](https://pat1one.github.io/faceit-ai-bot/)

</div>

---

## ✨ Возможности

<table>
<tr>
<td width="33%" align="center">

### 📊 Анализ статистики

Детальный анализ матчей<br/>
Отслеживание прогресса<br/>
Сравнение с другими игроками

</td>
<td width="33%" align="center">

### 👥 Поиск тиммейтов

Умные фильтры поиска<br/>
Статистика игроков<br/>
Удобная коммуникация

</td>
<td width="33%" align="center">

### 🔔 Уведомления

Новые матчи<br/>
Обновления статистики<br/>
Интеграция с Faceit

</td>
</tr>
</table>

## 🚀 Быстрый старт

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/pat1one/faceit-ai-bot.git
cd faceit-ai-bot

# Установить зависимости
make install

# Настроить окружение
cp .env.example .env
# Отредактируйте .env файл

# Собрать и запустить
make build
make deploy
```

### 🌐 Доступные сервисы

После запуска доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| 🎨 Frontend | http://localhost:3000 | Web интерфейс |
| ⚡ API | http://localhost:8000 | Backend API |
| 📖 API Docs | http://localhost:8000/docs | Swagger документация |
| 🗄️ PostgreSQL | localhost:5432 | База данных |

## 📦 Установка

### Вариант 1: Расширение для браузера

Легкий способ интеграции с Faceit

[⬇️ Скачать расширение](https://pat1one.github.io/faceit-ai-bot/)

### Вариант 2: Docker (полная версия)

Для локального развертывания всех сервисов

```bash
docker-compose up -d
```

## 🛠️ Технологии

<table>
<tr>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/nextjs/nextjs-original.svg" width="48" height="48" alt="Next.js"/>
<br><strong>Next.js 15</strong>
<br>React 19
</td>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/fastapi/fastapi-original.svg" width="48" height="48" alt="FastAPI"/>
<br><strong>FastAPI</strong>
<br>Python 3.9+
</td>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" width="48" height="48" alt="PostgreSQL"/>
<br><strong>PostgreSQL</strong>
<br>Database
</td>
<td align="center" width="25%">
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width="48" height="48" alt="Docker"/>
<br><strong>Docker</strong>
<br>Deployment
</td>
</tr>
</table>

## 📋 Основные команды

```bash
make help          # 📖 Показать все команды
make dev           # 🔧 Режим разработки
make build         # 🏗️ Собрать проект
make deploy        # 🚀 Деплой всех сервисов
make logs          # 📝 Показать логи
make stop          # ⏹️ Остановить сервисы
make clean         # 🧹 Очистить временные файлы
```

## 📁 Структура проекта

```text
faceit-ai-bot/
├── 📱 app/                 # Next.js приложение
├── ⚙️ src/                 # Backend + Browser Extension
│   ├── api/               # FastAPI endpoints
│   ├── ai/                # ML модели
│   └── services/          # Бизнес-логика
├── 🎨 public/             # Статические файлы
├── 🐳 docker-compose.yml  # Оркестрация сервисов
└── 📚 docs/               # Документация
```

## 📖 Документация

| Документ | Описание |
|----------|----------|
| 📘 [BUILD_DEPLOY.md](BUILD_DEPLOY.md) | Подробная инструкция по сборке и деплою |
| 🗺️ [ROADMAP.md](ROADMAP.md) | План развития проекта |
| 🚀 [QUICK_START.md](QUICK_START.md) | Быстрый старт для разработчиков |
| 🌐 [DEPLOY_PATTMSC_ONLINE.md](DEPLOY_PATTMSC_ONLINE.md) | Деплой на VPS |

## 🎯 Как использовать

1. **Установка** - Скачайте расширение или разверните полную версию
2. **Авторизация** - Войдите через Faceit аккаунт
3. **Анализ** - Начните анализировать статистику и искать тиммейтов

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта!

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'добавил крутую фичу'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

---

<div align="center">

**Сделано с ❤️ для CS2 комьюнити**

[⭐ Star](https://github.com/pat1one/faceit-ai-bot) • [🐛 Report Bug](https://github.com/pat1one/faceit-ai-bot/issues) • [💡 Request Feature](https://github.com/pat1one/faceit-ai-bot/issues)

</div>
