FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build React SPA
RUN apt-get update && apt-get install -y nodejs npm && \
    cd web && npm ci && npm run build && \
    rm -rf node_modules && \
    apt-get purge -y nodejs npm && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
