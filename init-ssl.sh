#!/bin/bash

# Проверяем, передан ли домен как аргумент
if [ -z "$1" ]; then
    echo "Использование: $0 your-domain.ru"
    exit 1
fi

DOMAIN=$1

# Создаем директории для certbot
mkdir -p certbot/conf
mkdir -p certbot/www

# Запускаем nginx
docker-compose up --force-recreate -d nginx

# Получаем SSL сертификат
docker-compose run --rm certbot certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email admin@$DOMAIN \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Перезапускаем nginx для применения сертификатов
docker-compose restart nginx