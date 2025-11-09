# Этап 1: Базовый образ для зависимостей
FROM python:3.9-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Настройка рабочей директории
WORKDIR /app

# Копируем только файлы зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Этап 2: Окончательный образ
FROM python:3.9-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 appuser

# Копирование установленных зависимостей из builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Установка рабочей директории
WORKDIR /app

# Копирование исходного кода
COPY src/ /app/src/
COPY main.py /app/

# Установка прав на файлы
RUN chown -R appuser:appuser /app

# Переключение на непривилегированного пользователя
USER appuser

# Проверка здоровья приложения
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "main.py"]