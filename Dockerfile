# Multi-stage Dockerfile for MP4SVG
FROM python:3.11-slim-bullseye as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# Development stage
FROM base as development

# Install development dependencies
RUN poetry install && rm -rf $POETRY_CACHE_DIR

# Copy source code
COPY . .

# Install package in development mode
RUN poetry install

EXPOSE 8000

CMD ["poetry", "run", "mp4svg-api"]

# Production stage
FROM base as production

# Create non-root user
RUN useradd --create-home --shell /bin/bash mp4svg

# Copy source code
COPY . .

# Install package
RUN poetry install --only=main
RUN poetry build
RUN pip install dist/*.whl

# Create data directory
RUN mkdir -p /app/data && chown mp4svg:mp4svg /app/data

# Switch to non-root user
USER mp4svg

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

# Default command runs API server
CMD ["mp4svg-api"]

# CLI stage for running CLI tools
FROM production as cli

USER root
RUN apt-get update && apt-get install -y vim nano && rm -rf /var/lib/apt/lists/*
USER mp4svg

CMD ["mp4svg-shell"]
