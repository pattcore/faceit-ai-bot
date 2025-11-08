#!/bin/bash

# Проверяем наличие параметра домена
if [ -z "$1" ]; then
    echo "Использование: $0 your-domain.com"
    exit 1
fi

DOMAIN=$1

# Устанавливаем NGINX и Certbot
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Создаем конфигурацию NGINX
sudo cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    server_name $DOMAIN;

    # Проксирование основного веб-приложения
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Проксирование API
    location /api/ {
        proxy_pass http://localhost:4000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Проксирование Grafana (опционально, с базовой аутентификацией)
    location /grafana/ {
        proxy_pass http://localhost:3001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF

# Создаем символическую ссылку
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Создаем пароль для доступа к Grafana через NGINX
sudo apt-get install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Проверяем конфигурацию NGINX
sudo nginx -t

# Получаем SSL-сертификат
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Перезапускаем NGINX
sudo systemctl restart nginx

echo "Настройка завершена!"
echo "Ваше приложение теперь доступно по адресу: https://$DOMAIN"
echo "API доступно по адресу: https://$DOMAIN/api"
echo "Grafana доступна по адресу: https://$DOMAIN/grafana"
echo "Не забудьте добавить A-запись в DNS-настройках домена, указывающую на IP-адрес сервера"
