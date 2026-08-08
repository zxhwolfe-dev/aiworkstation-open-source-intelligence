FROM python:3.12-slim

ARG OSI_IMAGE_COMMIT=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    OSI_IMAGE_COMMIT=${OSI_IMAGE_COMMIT}

LABEL org.opencontainers.image.revision=${OSI_IMAGE_COMMIT}

WORKDIR /app

RUN groupadd --system osi \
    && useradd --system --gid osi --home-dir /home/osi --create-home osi

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[mcp]"

USER osi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', int(__import__('os').environ.get('OSI_MCP_HTTP_PORT', '8000'))), 2); s.close()"

CMD ["osi-mcp-http"]
