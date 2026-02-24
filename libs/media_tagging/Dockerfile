FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.10.5 /uv /bin/
WORKDIR /build
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ADD requirements.txt .
RUN uv venv /opt/venv/ && \
  VIRTUAL_ENV=/opt/venv uv pip install -r requirements.txt --require-hashes --no-cache

FROM python:3.13-slim
RUN groupadd -r appuser && useradd -r -g  appuser appuser

ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1
COPY --from=builder /opt/venv/ /opt/venv/
WORKDIR /app/
COPY media_tagging/ ./media_tagging/
COPY pyproject.toml .

RUN chown -R appuser:appuser /app
EXPOSE 8000
ENV PYTHONPATH="/app"
USER appuser
ENTRYPOINT ["python", "-m",  "media_tagging.entrypoints.server", "--port", "8000"]
