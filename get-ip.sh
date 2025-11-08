#!/bin/bash
echo "Внешний IP-адрес сервера:"
curl -s ifconfig.me
echo -e "\n"
echo "Все сетевые интерфейсы:"
ip -brief addr show
