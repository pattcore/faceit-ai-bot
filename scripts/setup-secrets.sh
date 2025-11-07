#!/bin/bash

# Проверяем наличие переменной GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Пожалуйста, установите переменную GITHUB_TOKEN"
    echo "Вы можете создать токен здесь: https://github.com/settings/tokens"
    echo "Токен должен иметь права: repo, workflow"
    read -s -p "Введите ваш GitHub токен: " GITHUB_TOKEN
    echo
    export GITHUB_TOKEN
fi

# Определяем репозиторий из git remote
REMOTE_URL=$(git config --get remote.origin.url)
REPO=$(echo $REMOTE_URL | sed -E 's/.*github.com[:/](.+)\.git$/\1/')

echo "Добавление секретов в репозиторий $REPO"

# Запрашиваем данные Docker Hub
read -p "Введите ваш логин Docker Hub: " DOCKER_USERNAME
read -s -p "Введите ваш пароль/токен Docker Hub: " DOCKER_PASSWORD
echo

# Создаем публичный ключ для шифрования секретов
KEY_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/actions/secrets/public-key")

KEY_ID=$(echo $KEY_RESPONSE | jq -r .key_id)
PUBLIC_KEY=$(echo $KEY_RESPONSE | jq -r .key)

# Функция для шифрования значения с помощью sodium
encrypt_secret() {
    local value="$1"
    local public_key="$2"
    echo -n "$value" | sodium-cli box seal --public-key "$public_key" | base64
}

echo "Добавление DOCKER_USERNAME..."
ENCRYPTED_USERNAME=$(encrypt_secret "$DOCKER_USERNAME" "$PUBLIC_KEY")
curl -X PUT -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/actions/secrets/DOCKER_USERNAME" \
    -d "{\"encrypted_value\":\"$ENCRYPTED_USERNAME\",\"key_id\":\"$KEY_ID\"}"

echo "Добавление DOCKER_PASSWORD..."
ENCRYPTED_PASSWORD=$(encrypt_secret "$DOCKER_PASSWORD" "$PUBLIC_KEY")
curl -X PUT -H "Authorization: token $GITHUB_TOKEN" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/$REPO/actions/secrets/DOCKER_PASSWORD" \
    -d "{\"encrypted_value\":\"$ENCRYPTED_PASSWORD\",\"key_id\":\"$KEY_ID\"}"

echo "Секреты успешно добавлены!"

# Проверяем настройки Actions
curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/actions/permissions" | jq .enabled