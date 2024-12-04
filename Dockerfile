
FROM python:3.12-slim

LABEL authors="Игорь"

# Установка рабочего каталога
WORKDIR /app

# Установка необходимых системных зависимостей и poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

# Обновление PATH
ENV PATH="/root/.local/bin:$PATH"

# Копирование файлов для установки зависимостей
COPY pyproject.toml poetry.lock ./

# Установка зависимостей
RUN poetry install --no-root

# Копирование исходного кода
COPY . .

# Копирование crontab файла
COPY crontab /etc/cron.d/set_default_time

# Установка прав на файл crontab
RUN chmod 0644 /etc/cron.d/set_default_time

# Регистрация cron job
RUN crontab /etc/cron.d/set_default_time

# Запуск cron и основного приложения
CMD ["sh", "-c", "cron && poetry run python main.py"]
