# 🚀 Production Deployment Guide

## Quick Start with Docker Compose

### 1. Prerequisites
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### 2. Setup Environment
```bash
# Clone repository
git clone https://github.com/pattcore/faceit-ai-bot.git
cd faceit-ai-bot

# Copy and configure environment
cp .env.production.example .env.production
nano .env.production  # Fill with your values
```

### 3. Deploy
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check status
docker-compose -f docker-compose.prod.yml ps
```

---

## Manual Deployment (VPS/Dedicated Server)

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3-pip python3-venv \
    postgresql redis-server nginx git curl

# Create app directory
sudo mkdir -p /opt/faceit-ai-bot
sudo chown $USER:$USER /opt/faceit-ai-bot
```

### 2. Application Setup
```bash
cd /opt/faceit-ai-bot
git clone https://github.com/pattcore/faceit-ai-bot.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements-api-only.txt

# Configure environment
cp .env.example .env
nano .env  # Fill with your values
```

### 3. Database Setup
```bash
# Create PostgreSQL user and database
sudo -u postgres psql << EOF
CREATE USER faceit WITH PASSWORD 'your-password';
CREATE DATABASE faceit_prod OWNER faceit;
GRANT ALL PRIVILEGES ON DATABASE faceit_prod TO faceit;
\q
EOF

# Run migrations
alembic upgrade head
```

### 4. Setup Systemd Services
```bash
# Copy service files
sudo cp deployment/systemd/*.service /etc/systemd/system/

# Edit service files with your paths
sudo nano /etc/systemd/system/faceit-api.service
sudo nano /etc/systemd/system/faceit-celery-worker.service
sudo nano /etc/systemd/system/faceit-celery-beat.service

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable faceit-api faceit-celery-worker faceit-celery-beat
sudo systemctl start faceit-api faceit-celery-worker faceit-celery-beat

# Check status
sudo systemctl status faceit-api
```

### 5. Nginx Setup
```bash
# Copy nginx configuration
sudo cp nginx/nginx.conf /etc/nginx/sites-available/faceit-ai-bot
sudo ln -s /etc/nginx/sites-available/faceit-ai-bot /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret (min 32 chars)
- `GROQ_API_KEY` - Groq AI API key
- `FACEIT_API_KEY` - Faceit API key

### Optional
- `SENTRY_DSN` - Error tracking
- `SMTP_*` - Email notifications
- `YOOKASSA_*` - Payment processing

---

## Monitoring

### Logs
```bash
# API logs
sudo journalctl -u faceit-api -f

# Celery logs
sudo journalctl -u faceit-celery-worker -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
```

### Flower (Celery monitoring)
Access: `http://your-domain.com/flower`
Credentials: Set in `.env` (FLOWER_USER/FLOWER_PASSWORD)

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs  # API documentation
```

---

## Backup

### Database
```bash
# Backup
pg_dump -U faceit faceit_prod > backup.sql

# Restore
psql -U faceit faceit_prod < backup.sql
```

### Redis
```bash
# Backup
redis-cli SAVE
cp /var/lib/redis/dump.rdb /backup/redis-backup.rdb
```

---

## Update/Rollback

### Update
```bash
cd /opt/faceit-ai-bot
bash deployment/deploy.sh
```

### Rollback
```bash
git checkout <previous-commit>
sudo systemctl restart faceit-api
sudo systemctl restart faceit-celery-worker
```

---

## Troubleshooting

### Service won't start
```bash
sudo systemctl status faceit-api
sudo journalctl -u faceit-api -n 50
```

### Database connection issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U faceit -d faceit_prod -h localhost
```

### Redis connection issues
```bash
# Check Redis is running
sudo systemctl status redis

# Test connection
redis-cli ping
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall (ufw)
- [ ] Setup SSL certificates
- [ ] Configure rate limiting
- [ ] Enable Redis password
- [ ] Restrict Flower access
- [ ] Setup monitoring alerts
- [ ] Regular backups automated
- [ ] Update dependencies regularly

---

## Performance Optimization

### Database
```sql
-- Add indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
```

### Redis
```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Celery
- Adjust `concurrency` based on CPU cores
- Use separate queues for different task types
- Monitor task queue length

---

## Support

- GitHub Issues: https://github.com/pattcore/faceit-ai-bot/issues
- Documentation: https://github.com/pattcore/faceit-ai-bot
