FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn pydantic

COPY mock_endpoints/main.py /app/main.py

EXPOSE 11434 8088

CMD ["python", "/app/main.py"]
