from fastapi import (
    File,
    UploadFile,
    HTTPException,
    Request,
    Response,
    Query,
    APIRouter
)
from fastapi.responses import JSONResponse, HTMLResponse
import aiofiles
import psycopg2
import uuid
import os
from utils import validate_image, save_metadata
from config import UPLOAD_DIR, DB_CONFIG, templates, PAGE_SIZE
import logging
from typing import Any

router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    logging.info(f"Начинаем загрузку файла: {file.filename}")

    contents, file_size, file_type = await validate_image(file)

    # Генерируем уникальное имя с тем же расширением
    unique_filename = f"{uuid.uuid4().hex}{file_type}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Сначала пробуем сохранить метаданные
    if not save_metadata(unique_filename, file.filename, file_size // 1024, file_type.strip(".")):
        logging.error(f"Файл {file.filename} не сохранён - ошибка при записи метаданных")
        raise HTTPException(status_code=500, detail="Не удалось сохранить метаданные. Файл не сохранён.")

    # Если метаданные записаны - сохраняем файл
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(contents)
    except Exception as e:
        logging.error(f"Ошибка сохранения файла {unique_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при сохранении файла")

    url = f"/images/{unique_filename}"

    logging.info(
        f"Файл успешно загружен: {file.filename} сохранён как {unique_filename} URL: {url}"
    )

    return JSONResponse(content={"url": url})


@router.get("/images-list/", response_class=HTMLResponse)
async def images_list(
        request: Request,
        page: int = Query(1, ge=1),
        order: str = Query("DESC")
):
    total_pages = 0
    offset = (page - 1) * PAGE_SIZE

    order = order.upper()
    if order not in ("ASC", "DESC"):
        order = "DESC"

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM images")
                total_images = (cur.fetchone()).get("count")
                total_pages = (total_images + PAGE_SIZE - 1) // PAGE_SIZE
                cur.execute(f"SELECT * FROM images ORDER BY upload_time {order} LIMIT %s OFFSET %s",
                            (PAGE_SIZE, offset)
                            )
                files: list[dict[str, Any]] = cur.fetchall()
                for file in files:
                    upload_time = file.get('upload_time')
                    file['upload_time'] = upload_time.strftime("%Y-%m-%d %H:%M:%S") if upload_time else None

    except Exception as e:
        logging.error("Ошибка при выполнении запроса: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при выполнении запроса")

    return templates.TemplateResponse("images-list.html", {
        "request": request, "files": files, 'total_pages': total_pages, 'page': page, 'order': order
    })


@router.get("/delete/{id}")
async def delete_image(id: int, response: Response):
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM images WHERE id=%s RETURNING filename", (id,))
                file: dict[str, Any] = cur.fetchone()
                if file is None:
                    logging.warning("Запись с id=%s не найдена", id)
                    raise HTTPException(status_code=404, detail=f"Изображение с id={id} не найдено")
                else:
                    try:
                        file_path = os.path.join(UPLOAD_DIR, file.get('filename'))
                        os.remove(file_path)
                        logging.info("Файл %s успешно удалён", file_path)
                    except FileNotFoundError:
                        logging.warning("Файл %s не найден на диске", file_path)

                    conn.commit()
                    logging.info("Запись с id=%s успешно удалена из БД", id)
    except Exception as e:
        logging.error("Ошибка при удалении изображения с id=%s: %s", id, e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при выполнении запроса")

    response.headers["Location"] = "/images-list/"
    response.status_code = 302
    return {"message": "Redirected"}
