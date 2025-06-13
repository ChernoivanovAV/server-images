FROM python:3.13-slim

RUN apt-get update && \
    python -m ensurepip && \
    pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt --root-user-action=ignore


CMD ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
