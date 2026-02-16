FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/.huggingface \
    SENTENCE_TRANSFORMERS_HOME=/tmp/.cache/sentence-transformers


WORKDIR /app


# ==========================================
# Install system dependencies (CRITICAL)
# ==========================================

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        poppler-utils \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*


# Verify tesseract installed
RUN tesseract --version


# ==========================================
# Install Python dependencies
# ==========================================

COPY requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip && \
    python -m pip install -r /app/requirements.txt


# ==========================================
# Copy app
# ==========================================

COPY . /app


# ==========================================
# Expose port
# ==========================================

EXPOSE 7860


# ==========================================
# Run Flask
# ==========================================

CMD ["sh", "-c", "python -m flask --app web_app:app run --host 0.0.0.0 --port ${PORT:-7860}"]
