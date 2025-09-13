#!/bin/bash
# путь к файлу .env
ENV_FILE="./.env"

if [ ! -f "$ENV_FILE" ]; then
    echo ".env файл не найден!"
    exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

BACKUP_DIR="./backups"
CURRENT_DATE=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_$CURRENT_DATE.sql"
mkdir -p "$BACKUP_DIR"

docker exec -t "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Резервная копия успешно создана: $BACKUP_FILE"
else
    echo "Ошибка при создании резервной копии!"
fi

