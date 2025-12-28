# Multi-stage build para optimizar imagen
FROM python:3.11-slim as builder

# Variables de construcción
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Instalar dependencias del sistema necesarias para construcción
# (cacheable - only changes if deps change)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar SOLO requirements (cacheable layer)
COPY requirements.txt .

# Crear virtual environment y instalar dependencias
# (cached until requirements.txt changes)
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# ============================================================================
# Etapa final - imagen de producción
# ============================================================================
FROM python:3.11-slim

# Metadatos
LABEL maintainer="RAG Project Team" \
      description="Production-ready RAG API Server" \
      version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Crear usuario no-root por seguridad
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# Instalar solo runtime dependencies necesarios
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copiar venv desde builder (cached dependencies)
COPY --from=builder /opt/venv /opt/venv

# Copiar solo archivos de configuración y estructura (pequeño layer)
COPY --chown=appuser:appuser .env .env.example ./
COPY --chown=appuser:appuser src ./src

# Copiar assets/data si existen (opcional)
COPY --chown=appuser:appuser public ./public 2>/dev/null || true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Comando por defecto - ejecutar API con Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
