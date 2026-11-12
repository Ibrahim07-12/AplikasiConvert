FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# LibreOffice is required for DOC/DOCX, XLS/XLSX, and PPT/PPTX conversion.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY frontend ./frontend

EXPOSE 7860

# Hugging Face Docker Spaces exposes port 7860.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
