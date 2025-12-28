import psycopg2
import logging
from fastapi import (
    UploadFile,
    HTTPException
)
from config import DB_CONFIG, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
import os
from PIL import Image


def test_connection() -> None:
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        logging.info("Соединение с базой данных успешно")
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}", exc_info=True)
        raise


def save_metadata(filename: str, original_name: str, size: int, file_type: str) -> bool:
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                query = """
                        INSERT INTO images (filename, original_name, size, file_type)
                        VALUES (%s, %s, %s, %s) \
                        """
                cur.execute(query, (filename, original_name, size, file_type))
                conn.commit()
        logging.info(f"Метаданные успешно сохранены для файла {filename}")
        return True
    except Exception as e:
        logging.error(f"Ошибка сохранения метаданных: {e}", exc_info=True)
        return False


async def validate_image(file: UploadFile):
    logging.info(f"Проверка файла: {file.filename}")
    file_type = os.path.splitext(file.filename)[1].lower()

    # Проверяем расширение
    if file_type not in ALLOWED_EXTENSIONS:
        msg = f"Недопустимый формат файла: {file.filename}"
        logging.info(msg)
        raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены только .jpg, .png, .gif")

    # Проверяем размер
    contents = await file.read()
    file_size = len(contents)
    if file_size > MAX_FILE_SIZE:
        msg = f"Файл слишком большой: {file.filename} ({len(contents)} байт)"
        logging.info(msg)
        raise HTTPException(status_code=400, detail="Файл слишком большой. Максимум 5 МБ")

    # Проверяем, что файл - валидное изображение
    try:
        img = Image.open(file.file)
        img.verify()  # проверка целостности
    except Exception:
        msg = f"Файл не является валидным изображением: {file.filename}"
        logging.info(msg)
        raise HTTPException(status_code=400, detail="Загруженный файл не является валидным изображением")
    finally:
        file.file.seek(0)  # сбрасываем указатель, чтобы можно было читать файл заново

    logging.info(f"Файл прошел проверку: {file.filename}")
    return contents, file_size, file_type
