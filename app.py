import os
import logging
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import aiofiles
import uuid

app = FastAPI()

UPLOAD_DIR = "images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
LOG_FILE = "/app/logs/app.log"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Настройка логгера
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def allowed_file_extension(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


async def validate_image(file: UploadFile):
    logging.info(f"Проверка файла: {file.filename}")

    # Проверяем расширение
    if not allowed_file_extension(file.filename):
        msg = f"Недопустимый формат файла: {file.filename}"
        logging.info(msg)
        raise HTTPException(status_code=400, detail="Недопустимый формат файла. Разрешены только .jpg, .png, .gif")

    # Проверяем размер
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
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
    return contents


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    logging.info(f"Начинаем загрузку файла: {file.filename}")

    contents = await validate_image(file)

    # Получаем расширение оригинального файла
    ext = os.path.splitext(file.filename)[1].lower()

    # Генерируем уникальное имя с тем же расширением
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Асинхронно записываем файл
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(contents)

    url = f"/images/{unique_filename}"

    logging.info(f"Файл успешно загружен: {file.filename} сохранён как {unique_filename} URL: {url}")

    return JSONResponse(content={"url": url})
