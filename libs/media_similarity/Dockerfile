FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.10.5 /uv /bin/
WORKDIR /build
ENV UV_COMPILE_BYTECODE=0
ENV UV_LINK_MODE=copy
ADD requirements.txt .
RUN uv venv /opt/venv/ && \
  VIRTUAL_ENV=/opt/venv uv pip install -r requirements.txt --require-hashes --no-cache
WORKDIR /opt/venv/lib/python3.13/site-packages
RUN rm -rf googleapiclient/discovery_cache/documents
RUN rm -rf pandas/tests

FROM python:3.13-slim
RUN groupadd -r appuser && useradd -r -g  appuser appuser

ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1
COPY --from=builder /opt/venv/ /opt/venv/
WORKDIR /app/
COPY media_similarity/ ./media_similarity/
COPY pyproject.toml .

RUN chown -R appuser:appuser /app
EXPOSE 8000
ENV PYTHONPATH="/app"
USER appuser
CMD ["python", "-m",  "media_similarity.entrypoints.server", "--port", "8000"]
