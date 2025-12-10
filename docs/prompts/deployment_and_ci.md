# Deployment & CI/CD Guidance

## A. Dockerfile Template
Save as `docker/Dockerfile.ai`

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application Code
COPY cg_rera_extractor/ /app/cg_rera_extractor/
COPY scripts/ /app/scripts/

# Env Vars
ENV PYTHONUNBUFFERED=1
ENV MODEL_ROOT=/models

# Mount point for models (managed by volume)
VOLUME /models

CMD ["uvicorn", "cg_rera_extractor.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## B. Docker Compose (Production Snippet)

```yaml
version: '3.8'

services:
  ai_service:
    build:
      context: .
      dockerfile: docker/Dockerfile.ai
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - REDIS_URL=redis://redis:6379/0
      - MODEL_PATH=/models/production/v1/model.gguf
    volumes:
      - ./models_host:/models  # Mount host model directory
    depends_on:
      - postgres
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: db
    volumes:
      - pg_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine

volumes:
  pg_data:
```

## C. CI Pipeline (GitHub Actions)

File: `.github/workflows/ai_ci.yaml`

```yaml
name: AI Service CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Lint
        run: flake8 .
      - name: Unit Tests
        run: pytest tests/unit

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker Image
        run: docker build -t realmap-ai:latest -f docker/Dockerfile.ai .
      - name: Push to Registry
        run: |
          # echo ${{ secrets.DOCKER_PASSWORD }} | docker login ...
          # docker push realmap-ai:latest
```

## D. Kubernetes Notes
*   **Helm Values:**
    *   `image.repository`: `realmap-ai`
    *   `resources.limits.nvidia.com/gpu`: `1` (if using GPU node)
*   **Probes:**
    *   Liveness: `/health`
    *   Readiness: `/health` (ensure model is loaded)
*   **Node Selector:** `accelerator: nvidia-tesla-t4` or similar.

## E. Secrets & Artifacts
*   **Secrets:** Never commit `.env`. Use GitHub Secrets / K8s Secrets.
*   **Model Artifacts:**
    *   Do NOT commit `.gguf` files to Git.
    *   Store in S3 bucket: `s3://realmap-models/production/`.
    *   **Init Container:** Use an init container in K8s to run `aws s3 cp ...` to the shared volume before the app starts.
