#!/bin/bash

# Остановка текущих контейнеров
docker-compose down

# Переключение на ветку latest
git checkout latest
git pull origin latest

# Запуск docker-compose
docker-compose up --build -d
