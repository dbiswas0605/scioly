# Multi-stage build. The builder stage has full build tooling (gcc,
# libpq-dev) so pip can compile anything that doesn't ship a prebuilt wheel
# for this platform (arm64, when running on Raspberry Pi); the runtime
# stage only carries the resulting venv plus libpq's shared library.

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY . .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fs http://localhost:8000/api/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
