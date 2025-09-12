import logging
import os
import uuid

import aiofiles
import psycopg2
from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv('POSTGRES_DB'),
    "user": os.getenv('POSTGRES_USER'),
    "password": os.getenv('POSTGRES_PASSWORD'),
    "host": os.getenv('POSTGRES_HOST'),
    "port": 5432,
}

app = FastAPI()

UPLOAD_DIR = "images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
LOG_FILE = "./logs/app.log"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Настройка логгера
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


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


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    logging.info(f"Начинаем загрузку файла: {file.filename}")

    contents, file_size, file_type = await validate_image(file)

    # Генерируем уникальное имя с тем же расширением
    unique_filename = f"{uuid.uuid4().hex}{file_type}"

    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Асинхронно записываем файл
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(contents)

    url = f"/images/{unique_filename}"

    logging.info(
        f"Файл успешно загружен: {file.filename} сохранён как {unique_filename} URL: {url}"
    )

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor as cur:        
                cur.execute(
                    """
                    INSERT INTO images (filename, original_name, size, file_type)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (unique_filename, file.filename, file_size, file_type)
                )
                conn.commit()                
    except Exception as e:
        logging.error("Ошибка при выполнении запроса: %s", e, exc_info=True)

    return JSONResponse(content={"url": url})
