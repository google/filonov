FROM python:3.13-slim AS builder
WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1
ADD requirements.txt .
RUN python -m venv /opt/venv/ && \
  /opt/venv/bin/pip install -r requirements.txt --require-hashes --no-cache
RUN /opt/venv/bin/pip install opentelemetry-distro

RUN /opt/venv/bin/opentelemetry-bootstrap -a install
WORKDIR /opt/venv/lib/python3.13/site-packages
RUN rm -rf googleapiclient/discovery_cache/documents
RUN rm -rf pandas/tests

FROM python:3.13-slim
RUN groupadd -r appuser && useradd -r -g  appuser appuser

ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1
COPY --from=builder /opt/venv/ /opt/venv/
WORKDIR /opt/venv/
COPY media_similarity/ ./media_similarity/
COPY pyproject.toml .

RUN chown -R appuser:appuser /opt/venv/media_similarity
EXPOSE 8000
ENV PYTHONPATH="/opt/venv"
USER appuser
CMD ["uvicorn", "media_similarity.entrypoints.server:app", "--host", "0.0.0.0"]
