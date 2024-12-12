#!/bin/bash

# Остановка текущих контейнеров
docker-compose down

# Переключение на ветку stable
git checkout stable
git pull origin stable

# Запуск docker-compose
docker-compose up --build -d
