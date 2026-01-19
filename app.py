from fastapi import FastAPI
from contextlib import asynccontextmanager
from routers import router as main_router
from utils import test_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    test_connection()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)
