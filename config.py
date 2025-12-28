from dotenv import load_dotenv
import os
from psycopg2.extras import RealDictCursor
from fastapi.templating import Jinja2Templates
import logging

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv('POSTGRES_DB'),
    "user": os.getenv('POSTGRES_USER'),
    "password": os.getenv('POSTGRES_PASSWORD'),
    "host": os.getenv('POSTGRES_HOST'),
    "port": 5432,
    'cursor_factory': RealDictCursor
}

PAGE_SIZE = 10
templates = Jinja2Templates(directory='templates')

UPLOAD_DIR = "images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
LOG_FILE = "./logs/app.log"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Настройка логгера
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)