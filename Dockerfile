# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем зависимости для Python и системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота в контейнер
COPY . .

# Указываем команду для запуска чат-бота
CMD ["python", "main.py"]
