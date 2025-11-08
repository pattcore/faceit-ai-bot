#!/bin/bash

# Обновляем систему
sudo apt-get update
sudo apt-get upgrade -y

# Устанавливаем необходимые пакеты
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Добавляем текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Запускаем Docker
sudo systemctl enable docker
sudo systemctl start docker

echo "Установка завершена! Пожалуйста, перезайдите в систему для применения изменений группы docker"
