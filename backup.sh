#!/bin/bash
# путь к файлу .env
ENV_FILE="./.env"

if [ ! -f "$ENV_FILE" ]; then
    echo ".env файл не найден!"
    exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

if [ $# -eq 0 ]; then
  CURRENT_DATE=$(date +"%Y-%m-%d_%H%M%S")
  BACKUP_FILE="$BACKUP_DIR/backup_$CURRENT_DATE.sql"
  docker exec -t "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"

  if [ $? -eq 0 ]; then
      echo "Резервная копия успешно создана: $BACKUP_FILE"
  else
      rm "$BACKUP_FILE"
      echo "Ошибка при создании резервной копии!"
  fi
else
  RESTORE_FILE="$BACKUP_DIR/$1"

  if [ ! -f "$RESTORE_FILE" ]; then
    echo "!!! Файл $RESTORE_FILE не найден!"
    exit 1
  fi

  echo "!!! ВНИМАНИЕ: База данных $POSTGRES_DB будет восстановлена из файла $RESTORE_FILE"
  read -p "Продолжить? (y/n): " confirm
  if [ "$confirm" != "y" ]; then
    echo "Операция отменена."
    exit 0
  fi

  docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" "$POSTGRES_DB" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" "$POSTGRES_DB" < "$RESTORE_FILE"

  if [ $? -eq 0 ]; then
    echo "+++ База данных успешно восстановлена из $RESTORE_FILE"
  else
    echo "--- Ошибка при восстановлении базы данных"
  fi

fi