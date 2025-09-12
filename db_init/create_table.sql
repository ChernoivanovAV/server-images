CREATE TABLE images (
    id SERIAL PRIMARY KEY,               -- Уникальный идентификатор записи
    filename TEXT NOT NULL,              -- Уникальное имя файла (сгенерированное)
    original_name TEXT NOT NULL,         -- Оригинальное имя файла (пользователя)
    size INTEGER NOT NULL,               -- Размер файла в байтах
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Время загрузки файла
    file_type TEXT NOT NULL              -- Формат файла (jpg, png, gif и т.д.)
);
