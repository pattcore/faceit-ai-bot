# Настройка деплоя на VPS

## Необходимые GitHub Secrets

Добавьте следующие secrets в настройках репозитория:
**Settings → Secrets and variables → Actions → New repository secret**

### Обязательные secrets:

1. **VPS_SSH_PRIVATE_KEY**
   - Ваш приватный SSH ключ для подключения к VPS
   - Получить: `cat ~/.ssh/id_rsa` (на вашей локальной машине)
   - Или создать новый: `ssh-keygen -t rsa -b 4096`

2. **VPS_HOST**
   - IP адрес или домен вашего VPS
   - Пример: `123.45.67.89` или `vps.example.com`

3. **VPS_USER**
   - Пользователь для SSH подключения
   - Пример: `root` или `ubuntu`

4. **VPS_PORT** (опционально)
   - SSH порт (по умолчанию 22)
   - Пример: `22` или `2222`

5. **VPS_DEPLOY_PATH**
   - Путь на VPS где будет развернуто приложение
   - Пример: `/var/www/faceit-ai-bot` или `/home/ubuntu/app`

## Подготовка VPS

### 1. Установка Docker на VPS

```bash
# Подключитесь к VPS
ssh user@your-vps-ip

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установите Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Перезайдите в систему для применения изменений
exit
```

### 2. Настройка SSH ключа

На вашей локальной машине:

```bash
# Сгенерируйте SSH ключ (если еще нет)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/vps_deploy_key

# Скопируйте публичный ключ на VPS
ssh-copy-id -i ~/.ssh/vps_deploy_key.pub user@your-vps-ip

# Проверьте подключение
ssh -i ~/.ssh/vps_deploy_key user@your-vps-ip
```

Теперь скопируйте содержимое приватного ключа в GitHub Secret:

```bash
cat ~/.ssh/vps_deploy_key
```

### 3. Создание директории на VPS

```bash
ssh user@your-vps-ip
sudo mkdir -p /var/www/faceit-ai-bot
sudo chown $USER:$USER /var/www/faceit-ai-bot
```

### 4. Настройка .env на VPS

Создайте `.env` файл на VPS:

```bash
cd /var/www/faceit-ai-bot
nano .env
```

Добавьте необходимые переменные окружения:

```env
DATABASE_URL=postgresql://faceit:faceit@db:5432/faceit
API_HOST=0.0.0.0
API_PORT=8000
NODE_ENV=production
SECRET_KEY=your-production-secret-key
REDIS_URL=redis://localhost:6379
YOOKASSA_SHOP_ID=your-shop-id
YOOKASSA_SECRET_KEY=your-secret-key
```

### 5. Настройка firewall (опционально)

```bash
# Разрешите необходимые порты
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Frontend (если нужен прямой доступ)
sudo ufw allow 8000/tcp  # API (если нужен прямой доступ)
sudo ufw enable
```

## Запуск деплоя

### Автоматический деплой

При каждом push в ветку `main` будет автоматически запущен деплой на VPS.

### Ручной деплой

Перейдите в GitHub Actions → Deploy to VPS → Run workflow

## Проверка деплоя

После успешного деплоя проверьте:

```bash
# Подключитесь к VPS
ssh user@your-vps-ip

# Проверьте статус контейнеров
docker-compose ps

# Проверьте логи
docker-compose logs -f

# Проверьте API
curl http://localhost:8000/health

# Проверьте Frontend
curl http://localhost:3000
```

## Доступ к приложению

- Frontend: `http://your-vps-ip:3000`
- API: `http://your-vps-ip:8000`
- API Docs: `http://your-vps-ip:8000/docs`

## Настройка домена (опционально)

Если у вас есть домен, настройте Nginx reverse proxy:

```bash
# Установите Nginx
sudo apt-get install nginx

# Настройте конфиг (используйте setup-nginx-ssl.sh из проекта)
bash setup-nginx-ssl.sh your-domain.com
```

## Troubleshooting

### Проблемы с SSH

```bash
# Проверьте SSH подключение вручную
ssh -v user@your-vps-ip

# Проверьте права на ключ
chmod 600 ~/.ssh/vps_deploy_key
```

### Проблемы с Docker

```bash
# Перезапустите Docker
sudo systemctl restart docker

# Очистите старые образы
docker system prune -a
```

### Логи деплоя

Смотрите логи GitHub Actions для детальной информации об ошибках.
