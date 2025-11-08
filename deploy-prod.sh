#!/bin/bash

# Настройки
APP_DIR="/opt/faceit-ai-bot"
GITHUB_REPO="https://github.com/pat1one/faceit-ai-bot.git"

# Создаем директорию приложения
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Клонируем или обновляем репозиторий
if [ -d "$APP_DIR/.git" ]; then
    echo "Обновляем репозиторий..."
    cd $APP_DIR
    git pull
else
    echo "Клонируем репозиторий..."
    git clone $GITHUB_REPO $APP_DIR
    cd $APP_DIR
fi

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    echo "Создаем .env файл..."
    cat > .env << EOF
NODE_ENV=production
DATABASE_URL=postgresql://faceit:faceit@db:5432/faceit
REDIS_URL=redis://redis:6379
# Добавьте другие переменные окружения здесь
EOF
fi

# Запускаем Docker Compose
echo "Запускаем приложение..."
docker-compose -f docker-compose.yml up -d --build

echo "Деплой завершен!"
echo "Проверьте работу приложения по адресу: http://ваш-ip:3000"
