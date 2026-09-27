FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    iproute2 \
    iputils-ping \
    mtr-tiny \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn requests prometheus_client starlette

COPY prober/path_prober.py /app/path_prober.py

EXPOSE 9200

CMD ["python", "/app/path_prober.py"]
