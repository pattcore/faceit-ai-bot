# Быстрый старт - Faceit AI Bot

## Самый простой способ запустить проект

### Вариант 1: Используя Makefile (рекомендуется)

```bash
# Установить зависимости
make install

# Создать .env файл
cp .env.example .env

# Собрать и запустить всё
make build
make deploy
```

### Вариант 2: Используя bash скрипты

```bash
# Установить зависимости
npm install

# Создать .env файл
cp .env.example .env

# Собрать всё
chmod +x build-all.sh
./build-all.sh

# Запустить всё
chmod +x deploy.sh
./deploy.sh
```

### Вариант 3: Только для разработки (без Docker)

```bash
# Установить зависимости
npm install

# Создать .env файл
cp .env.example .env

# Запустить только базу данных
chmod +x dev.sh
./dev.sh

# В отдельном терминале - frontend
npm run dev

# В другом терминале - backend
python main.py
```

## Доступ к сервисам

После запуска откройте в браузере:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Документация: http://localhost:8000/docs

## Полезные команды

```bash
make help          # Показать все доступные команды
make logs          # Посмотреть логи всех сервисов
make stop          # Остановить все сервисы
make restart       # Перезапустить сервисы
make clean         # Очистить временные файлы
```

## Проблемы?

Смотрите подробную документацию: [BUILD_DEPLOY.md](BUILD_DEPLOY.md)

## Готово

Теперь вы можете начать работу с Faceit AI Bot!
