#!/bin/bash

# Остановка и удаление старого контейнера, если он существует
docker stop faceit-ai-bot || true
docker rm faceit-ai-bot || true

# Сборка нового образа
docker build -t faceit-ai-bot .

# Запуск нового контейнера
docker run -d \
    --name faceit-ai-bot \
    --restart unless-stopped \
    -p 8000:8000 \
    -v $(pwd)/data:/app/data \
    -v $(pwd)/logs:/app/logs \
    --env-file .env \
    faceit-ai-bot