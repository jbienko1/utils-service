FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-pol \
        poppler-utils \
        pandoc \
        plantuml \
        graphviz \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY mermaid-cli/package.json mermaid-cli/package-lock.json ./mermaid-cli/

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
RUN cd mermaid-cli && npm ci --omit=dev

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
