#!/bin/bash

# Проверяем наличие параметра домена
if [ -z "$1" ]; then
    echo "Использование: $0 pattmsc.online"
    exit 1
fi

DOMAIN=$1
API_DOMAIN="api.$DOMAIN"
MONITOR_DOMAIN="monitor.$DOMAIN"

# Устанавливаем NGINX и Certbot
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Конфигурация для основного домена
sudo cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    server_name $DOMAIN;
    
    # Увеличиваем размер загружаемых файлов
    client_max_body_size 50M;
    
    # Включаем сжатие
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        
        # Добавляем заголовки безопасности
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Content-Type-Options "nosniff";
    }
}
EOF

# Конфигурация для API поддомена
sudo cat > /etc/nginx/sites-available/$API_DOMAIN << EOF
server {
    server_name $API_DOMAIN;
    
    # Увеличиваем таймауты для долгих запросов
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    
    location / {
        proxy_pass http://localhost:4000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' 'https://$DOMAIN';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
    }
}
EOF

# Конфигурация для мониторинга
sudo cat > /etc/nginx/sites-available/$MONITOR_DOMAIN << EOF
server {
    server_name $MONITOR_DOMAIN;
    
    # Базовая аутентификация для безопасности
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
    
    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Создаем символические ссылки
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/$API_DOMAIN /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/$MONITOR_DOMAIN /etc/nginx/sites-enabled/

# Создаем пароль для доступа к мониторингу
sudo apt-get install -y apache2-utils
echo "Создание пароля для доступа к мониторингу (monitor.$DOMAIN):"
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Проверяем конфигурацию NGINX
sudo nginx -t

# Получаем SSL-сертификаты для всех доменов
sudo certbot --nginx -d $DOMAIN -d $API_DOMAIN -d $MONITOR_DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Перезапускаем NGINX
sudo systemctl restart nginx

echo "Настройка завершена!"
echo ""
echo "Ваши сервисы доступны по следующим адресам:"
echo "Основной сайт: https://$DOMAIN"
echo "API: https://$API_DOMAIN"
echo "Мониторинг: https://$MONITOR_DOMAIN"
echo ""
echo "Теперь необходимо добавить следующие A-записи в DNS-настройках на Reg.ru:"
echo ""
echo "1. Для основного домена:"
echo "Тип: A"
echo "Имя: @"
echo "Значение: [IP вашего сервера]"
echo ""
echo "2. Для API:"
echo "Тип: A"
echo "Имя: api"
echo "Значение: [IP вашего сервера]"
echo ""
echo "3. Для мониторинга:"
echo "Тип: A"
echo "Имя: monitor"
echo "Значение: [IP вашего сервера]"
