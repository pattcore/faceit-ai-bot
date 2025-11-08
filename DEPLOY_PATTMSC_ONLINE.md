# Деплой на pattmsc.online

## 🎯 Быстрая настройка для вашего домена

Ваш домен: **pattmsc.online**

---

## 1️⃣ Подготовка VPS на reg.ru

### Подключение к серверу

```bash
ssh root@pattmsc.online
# или используйте IP адрес если DNS еще не настроен
```

### Установка необходимого ПО

```bash
# Обновление системы
apt-get update && apt-get upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка Docker Compose
apt-get install docker-compose-plugin -y

# Проверка
docker --version
docker compose version
```

---

## 2️⃣ Настройка SSH ключа для деплоя

### На вашей локальной машине (Windows):

```powershell
# Откройте PowerShell и выполните:
ssh-keygen -t rsa -b 4096 -f $HOME\.ssh\pattmsc_deploy_key

# Просмотрите публичный ключ
Get-Content $HOME\.ssh\pattmsc_deploy_key.pub
```

### На VPS (pattmsc.online):

```bash
# Создайте директорию для SSH
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавьте публичный ключ
nano ~/.ssh/authorized_keys
# Вставьте содержимое pattmsc_deploy_key.pub
# Сохраните: Ctrl+O, Enter, Ctrl+X

chmod 600 ~/.ssh/authorized_keys
```

### Проверка подключения:

```powershell
ssh -i $HOME\.ssh\pattmsc_deploy_key root@pattmsc.online
```

---

## 3️⃣ Создание структуры на VPS

```bash
# На VPS
mkdir -p /var/www/faceit-ai-bot
cd /var/www/faceit-ai-bot

# Создайте .env файл
nano .env
```

### Содержимое .env:

```env
# Database
DATABASE_URL=postgresql://faceit:FaceitSecure2024!@db:5432/faceit

# API
API_HOST=0.0.0.0
API_PORT=8000

# Node/Next
NODE_ENV=production

# Security
SECRET_KEY=pattmsc-online-super-secure-key-change-this-12345

# Redis
REDIS_URL=redis://localhost:6379

# Payment providers (заполните свои данные)
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
SBP_API_URL=
SBP_TOKEN=

# Testing
TEST_ENV=false
```

**⚠️ ВАЖНО:** Измените `SECRET_KEY` на уникальное значение!

---

## 4️⃣ Настройка GitHub Secrets

Перейдите в ваш репозиторий:
**https://github.com/pat1one/faceit-ai-bot/settings/secrets/actions**

### Добавьте следующие secrets:

#### VPS_SSH_PRIVATE_KEY
```powershell
# На Windows PowerShell:
Get-Content $HOME\.ssh\pattmsc_deploy_key
```
Скопируйте **весь вывод** включая:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

#### VPS_HOST
```
pattmsc.online
```

#### VPS_USER
```
root
```

#### VPS_PORT
```
22
```

#### VPS_DEPLOY_PATH
```
/var/www/faceit-ai-bot
```

---

## 5️⃣ Настройка DNS на reg.ru

В панели управления доменом `pattmsc.online` добавьте A-записи:

```
Тип    Имя              Значение           TTL
A      @                ВАШ_IP_АДРЕС       3600
A      www              ВАШ_IP_АДРЕС       3600
A      api              ВАШ_IP_АДРЕС       3600
```

Где `ВАШ_IP_АДРЕС` - это IP адрес вашего VPS на reg.ru.

**Проверка DNS:**
```bash
nslookup pattmsc.online
nslookup api.pattmsc.online
```

---

## 6️⃣ Настройка Nginx на VPS

```bash
# Установите Nginx
apt-get install nginx -y

# Создайте конфигурацию
nano /etc/nginx/sites-available/pattmsc.online
```

### Конфигурация Nginx:

```nginx
# Frontend - pattmsc.online
server {
    listen 80;
    server_name pattmsc.online www.pattmsc.online;

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

# API - api.pattmsc.online
server {
    listen 80;
    server_name api.pattmsc.online;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### Активация конфигурации:

```bash
# Создайте символическую ссылку
ln -s /etc/nginx/sites-available/pattmsc.online /etc/nginx/sites-enabled/

# Проверьте конфигурацию
nginx -t

# Перезапустите Nginx
systemctl restart nginx
```

---

## 7️⃣ Установка SSL сертификата (HTTPS)

```bash
# Установите Certbot
apt-get install certbot python3-certbot-nginx -y

# Получите SSL сертификат для всех доменов
certbot --nginx -d pattmsc.online -d www.pattmsc.online -d api.pattmsc.online

# Следуйте инструкциям:
# 1. Введите email
# 2. Согласитесь с условиями (Y)
# 3. Выберите опцию 2 (Redirect HTTP to HTTPS)
```

Certbot автоматически:
- Получит сертификаты
- Настроит Nginx для HTTPS
- Настроит автоматическое обновление

**Проверка автообновления:**
```bash
certbot renew --dry-run
```

---

## 8️⃣ Настройка Firewall

```bash
# Разрешите необходимые порты
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS

# Включите firewall
ufw enable

# Проверьте статус
ufw status
```

---

## 9️⃣ Первый деплой

### Вариант 1: Автоматический (через GitHub Actions)

Просто сделайте push:
```bash
git add .
git commit -m "Deploy to pattmsc.online"
git push origin main
```

GitHub Actions автоматически задеплоит приложение!

### Вариант 2: Ручной деплой

Перейдите на GitHub:
**Actions → Deploy to VPS → Run workflow → Run workflow**

---

## 🔟 Проверка работы

### После деплоя проверьте:

**На VPS:**
```bash
# Подключитесь к VPS
ssh root@pattmsc.online

# Проверьте контейнеры
cd /var/www/faceit-ai-bot
docker compose ps

# Должны быть запущены:
# - faceit-ai-bot-web-1
# - faceit-ai-bot-api-1
# - faceit-ai-bot-db-1

# Проверьте логи
docker compose logs -f
```

**В браузере:**
- Frontend: https://pattmsc.online
- API: https://api.pattmsc.online
- API Docs: https://api.pattmsc.online/docs
- Health Check: https://api.pattmsc.online/health

---

## 📊 Мониторинг и управление

### Просмотр логов

```bash
# Все логи
docker compose logs -f

# Логи frontend
docker compose logs -f web

# Логи API
docker compose logs -f api

# Логи базы данных
docker compose logs -f db

# Последние 100 строк
docker compose logs --tail=100
```

### Управление сервисами

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

# Пересборка (после изменений кода)
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Обновление приложения

После push в GitHub:
1. GitHub Actions автоматически деплоит
2. Или запустите вручную: **Actions → Deploy to VPS → Run workflow**

---

## 🔧 Troubleshooting

### Проблема: Сайт не открывается

```bash
# Проверьте контейнеры
docker compose ps

# Проверьте Nginx
systemctl status nginx
nginx -t

# Проверьте логи
docker compose logs
tail -f /var/log/nginx/error.log
```

### Проблема: SSL не работает

```bash
# Проверьте сертификаты
certbot certificates

# Обновите сертификаты
certbot renew --force-renewal
systemctl restart nginx
```

### Проблема: GitHub Actions падает

1. Проверьте все secrets настроены правильно
2. Проверьте SSH подключение вручную:
   ```powershell
   ssh -i $HOME\.ssh\pattmsc_deploy_key root@pattmsc.online
   ```
3. Проверьте логи в GitHub Actions
4. Проверьте права на директорию:
   ```bash
   ls -la /var/www/faceit-ai-bot
   ```

### Проблема: База данных не запускается

```bash
# Проверьте логи БД
docker compose logs db

# Проверьте volumes
docker volume ls

# Пересоздайте БД (ОСТОРОЖНО: удалит данные!)
docker compose down -v
docker compose up -d
```

---

## 💾 Автоматические бэкапы

### Создайте скрипт бэкапа:

```bash
nano /root/backup-faceit.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups/faceit"
mkdir -p $BACKUP_DIR

cd /var/www/faceit-ai-bot

# Бэкап базы данных
docker compose exec -T db pg_dump -U faceit faceit > $BACKUP_DIR/db_$DATE.sql
gzip $BACKUP_DIR/db_$DATE.sql

# Бэкап .env файла
cp .env $BACKUP_DIR/env_$DATE.backup

# Удалить старые бэкапы (старше 14 дней)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +14 -delete
find $BACKUP_DIR -name "env_*.backup" -mtime +14 -delete

echo "✅ Backup completed: $DATE"
```

```bash
chmod +x /root/backup-faceit.sh

# Добавьте в crontab (бэкап каждый день в 3:00)
crontab -e
# Добавьте строку:
0 3 * * * /root/backup-faceit.sh >> /var/log/backup-faceit.log 2>&1
```

---

## 📈 Мониторинг ресурсов

```bash
# Мониторинг в реальном времени
htop

# Использование Docker
docker stats

# Дисковое пространство
df -h

# Память
free -h

# Сетевые подключения
netstat -tulpn | grep LISTEN
```

---

## 🎉 Готово!

Ваше приложение теперь доступно по адресам:

- 🌐 **Frontend:** https://pattmsc.online
- 🔌 **API:** https://api.pattmsc.online
- 📚 **API Docs:** https://api.pattmsc.online/docs

### Автоматический деплой настроен!
Каждый `git push` в ветку `main` будет автоматически обновлять приложение на сервере.

---

## 📞 Полезные ссылки

- GitHub репозиторий: https://github.com/pat1one/faceit-ai-bot
- GitHub Actions: https://github.com/pat1one/faceit-ai-bot/actions
- Общая документация: См. `README.md`, `VPS_SETUP.md`, `DEPLOY_REGRU.md`
