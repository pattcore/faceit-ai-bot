#!/bin/bash

# Проверяем, переданы ли все аргументы
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Использование: $0 your-domain.ru user@server-ip"
    exit 1
fi

DOMAIN=$1
SERVER=$2

# Создаем необходимые директории на сервере
ssh $SERVER "mkdir -p ~/faceit-ai-bot"

# Копируем файлы на сервер
rsync -avz --exclude 'node_modules' \
    --exclude '.git' \
    --exclude 'certbot' \
    --exclude '.env' \
    ./ $SERVER:~/faceit-ai-bot/

# Копируем .env файл отдельно (убедитесь, что он существует локально)
scp .env $SERVER:~/faceit-ai-bot/.env

# Устанавливаем Docker и Docker Compose на сервере
ssh $SERVER "curl -fsSL https://get.docker.com | sh && \
    sudo systemctl enable docker && \
    sudo systemctl start docker && \
    sudo curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose && \
    sudo chmod +x /usr/local/bin/docker-compose"

# Запускаем инициализацию SSL
ssh $SERVER "cd ~/faceit-ai-bot && chmod +x init-ssl.sh && ./init-ssl.sh $DOMAIN"

# Запускаем приложение
ssh $SERVER "cd ~/faceit-ai-bot && docker-compose up -d"

echo "Деплой завершен. Проверьте $DOMAIN"