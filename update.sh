
   #!/bin/bash

   # Стянуть последнюю версию с GitHub
   git pull origin main

   # Пересобрать образ и перезапустить контейнеры
   docker-compose down
   docker-compose up --build -d
