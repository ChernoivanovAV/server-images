FROM python:3.13-slim

RUN apt-get update && apt-get install -y postgresql-client nano mc libpq-dev gcc && \
    python -m ensurepip && \
    pip install --no-cache-dir --upgrade pip && \
    rm -rf /var/lib/apt/lists/*



WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY .env /app/.env
COPY wait-for-it.sh /app/wait-for-it.sh
RUN chmod +x /app/wait-for-it.sh

RUN pip install --no-cache-dir -r requirements.txt --root-user-action=ignore

RUN apt-get remove -y gcc && \
    apt-get autoremove -y

CMD ["./wait-for-it.sh", "db:5432", "--", "uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
