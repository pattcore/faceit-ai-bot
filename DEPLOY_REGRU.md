# Деплой на reg.ru через GitHub Actions

## Подготовка VPS на reg.ru

### 1. Подключение к VPS

```bash
# Подключитесь к вашему VPS
ssh root@your-domain.ru
# или
ssh root@your-ip-address
```

### 2. Установка Docker и Docker Compose

```bash
# Обновите систему
apt-get update && apt-get upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установите Docker Compose
apt-get install docker-compose-plugin -y

# Проверьте установку
docker --version
docker compose version
```

### 3. Создание пользователя для деплоя (рекомендуется)

```bash
# Создайте пользователя
adduser deploy
usermod -aG docker deploy
usermod -aG sudo deploy

# Переключитесь на пользователя
su - deploy
```

### 4. Настройка SSH ключа

На вашей **локальной машине**:

```bash
# Сгенерируйте SSH ключ для деплоя
ssh-keygen -t rsa -b 4096 -f ~/.ssh/regru_deploy_key -C "deploy@faceit-ai-bot"

# Скопируйте публичный ключ
cat ~/.ssh/regru_deploy_key.pub
```

На **VPS (reg.ru)**:

```bash
# Создайте директорию для SSH ключей
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавьте публичный ключ
nano ~/.ssh/authorized_keys
# Вставьте содержимое regru_deploy_key.pub
# Сохраните: Ctrl+O, Enter, Ctrl+X

chmod 600 ~/.ssh/authorized_keys
```

Проверьте подключение:

```bash
ssh -i ~/.ssh/regru_deploy_key deploy@your-domain.ru
```

### 5. Создание директории для приложения

```bash
# На VPS
mkdir -p /home/deploy/faceit-ai-bot
cd /home/deploy/faceit-ai-bot
```

### 6. Настройка .env файла

```bash
# Создайте .env файл
nano .env
```

Добавьте:

```env
# Database
DATABASE_URL=postgresql://faceit:faceit_secure_password@db:5432/faceit

# API
API_HOST=0.0.0.0
API_PORT=8000

# Node/Next
NODE_ENV=production

# Security
SECRET_KEY=your-super-secure-secret-key-change-this

# Redis (если используется)
REDIS_URL=redis://localhost:6379

# Payment providers
YOOKASSA_SHOP_ID=your-shop-id
YOOKASSA_SECRET_KEY=your-secret-key
SBP_API_URL=
SBP_TOKEN=

# Testing
TEST_ENV=false
```

**⚠️ Важно:** Измените `SECRET_KEY` и пароли на безопасные значения!

## Настройка GitHub Secrets

Перейдите в ваш репозиторий на GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

### Добавьте следующие secrets:

#### 1. VPS_SSH_PRIVATE_KEY
```bash
# На локальной машине выполните:
cat ~/.ssh/regru_deploy_key
```
Скопируйте **весь вывод** (включая `-----BEGIN` и `-----END`) и вставьте в GitHub Secret.

#### 2. VPS_HOST
Ваш домен или IP адрес:
- Если есть домен: `your-domain.ru`
- Если только IP: `123.45.67.89`

#### 3. VPS_USER
Пользователь для SSH:
- Если создали пользователя `deploy`: `deploy`
- Если используете root: `root`

#### 4. VPS_PORT (опционально)
SSH порт (по умолчанию `22`):
- Стандартный порт: `22`
- Если изменили: укажите свой порт

#### 5. VPS_DEPLOY_PATH
Путь к директории приложения:
```
/home/deploy/faceit-ai-bot
```
или
```
/root/faceit-ai-bot
```

## Настройка домена на reg.ru

### 1. DNS записи

В панели управления reg.ru добавьте A-записи:

```
A    @              123.45.67.89    (ваш IP)
A    www            123.45.67.89    (ваш IP)
A    api            123.45.67.89    (для API)
```

### 2. Настройка Nginx на VPS

```bash
# Установите Nginx
sudo apt-get install nginx -y

# Создайте конфигурацию
sudo nano /etc/nginx/sites-available/faceit-ai-bot
```

Добавьте конфигурацию:

```nginx
# Frontend
server {
    listen 80;
    server_name your-domain.ru www.your-domain.ru;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API
server {
    listen 80;
    server_name api.your-domain.ru;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/faceit-ai-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Установка SSL сертификата (Let's Encrypt)

```bash
# Установите certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Получите сертификат
sudo certbot --nginx -d your-domain.ru -d www.your-domain.ru -d api.your-domain.ru

# Автоматическое обновление
sudo certbot renew --dry-run
```

## Настройка Firewall

```bash
# Разрешите необходимые порты
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
sudo ufw status
```

## Запуск деплоя

### Автоматический деплой

После настройки всех secrets, каждый `git push` в ветку `main` будет автоматически деплоить приложение на ваш VPS.

```bash
git add .
git commit -m "Deploy to reg.ru"
git push origin main
```

### Ручной деплой

Перейдите в GitHub:
**Actions → Deploy to VPS → Run workflow → Run workflow**

## Проверка деплоя

### На VPS

```bash
# Подключитесь к VPS
ssh -i ~/.ssh/regru_deploy_key deploy@your-domain.ru

# Перейдите в директорию
cd /home/deploy/faceit-ai-bot

# Проверьте статус контейнеров
docker compose ps

# Проверьте логи
docker compose logs -f

# Проверьте отдельные сервисы
docker compose logs web
docker compose logs api
docker compose logs db
```

### Через браузер

- Frontend: `https://your-domain.ru`
- API: `https://api.your-domain.ru`
- API Docs: `https://api.your-domain.ru/docs`
- Health check: `https://api.your-domain.ru/health`

## Полезные команды

### Управление контейнерами

```bash
# Перезапуск всех сервисов
docker compose restart

# Перезапуск конкретного сервиса
docker compose restart web
docker compose restart api

# Остановка
docker compose down

# Запуск
docker compose up -d

# Пересборка
docker compose build --no-cache
docker compose up -d
```

### Просмотр логов

```bash
# Все логи
docker compose logs -f

# Последние 100 строк
docker compose logs --tail=100

# Логи конкретного сервиса
docker compose logs -f api
```

### Очистка

```bash
# Удалить неиспользуемые образы
docker system prune -a

# Удалить volumes (ОСТОРОЖНО: удалит данные БД!)
docker compose down -v
```

## Troubleshooting

### Проблема: Контейнеры не запускаются

```bash
# Проверьте логи
docker compose logs

# Проверьте .env файл
cat .env

# Пересоберите без кэша
docker compose build --no-cache
docker compose up -d
```

### Проблема: Сайт недоступен

```bash
# Проверьте Nginx
sudo nginx -t
sudo systemctl status nginx

# Проверьте firewall
sudo ufw status

# Проверьте DNS
nslookup your-domain.ru
```

### Проблема: SSL не работает

```bash
# Проверьте сертификаты
sudo certbot certificates

# Обновите сертификаты
sudo certbot renew --force-renewal
```

### Проблема: GitHub Actions падает

1. Проверьте все secrets настроены
2. Проверьте SSH подключение вручную
3. Проверьте логи в GitHub Actions
4. Проверьте права на директорию на VPS

## Мониторинг

### Настройка мониторинга (опционально)

```bash
# Установите htop для мониторинга ресурсов
sudo apt-get install htop -y

# Мониторинг Docker
docker stats

# Мониторинг дискового пространства
df -h

# Мониторинг памяти
free -h
```

## Бэкапы

### Бэкап базы данных

```bash
# Создайте скрипт для бэкапа
nano ~/backup-db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/deploy/backups"
mkdir -p $BACKUP_DIR

docker compose exec -T db pg_dump -U faceit faceit > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Удалить старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

```bash
chmod +x ~/backup-db.sh

# Добавьте в crontab для автоматического бэкапа
crontab -e
# Добавьте строку (бэкап каждый день в 3:00):
0 3 * * * /home/deploy/backup-db.sh
```

## Контакты и поддержка

- GitHub Issues: https://github.com/pat1one/faceit-ai-bot/issues
- Документация: См. README.md и другие .md файлы в проекте

---

**Готово!** После выполнения всех шагов ваше приложение будет автоматически деплоиться на reg.ru при каждом push в main.
