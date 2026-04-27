# Базовый образ Python
FROM python:3.11-slim

# Установка системных зависимостей (только необходимые)
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей (с кэшированием)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Копирование проекта
COPY . .

# Создание директорий для статики и медиа
RUN mkdir -p /app/static /app/media

# Сбор статических файлов
RUN python manage.py collectstatic --noinput

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]