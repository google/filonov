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
RUN rm -rf numpy/**/tests
RUN rm -rf \
    pyarrow/libarrow_flight.so* \
    pyarrow/libarrow_flight_sql.so* \
    pyarrow/libarrow_python_flight.so* \
    pyarrow/libarrow_dataset.so* \
    pyarrow/libarrow_acero.so* \
    pyarrow/libgandiva.so* \
    pyarrow/libarrow_substrait.so*

FROM python:3.13-slim
RUN groupadd -r appuser && useradd -r -g  appuser appuser

ENV PATH="/opt/venv/bin:$PATH" \
  PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1
COPY --from=builder /opt/venv/ /opt/venv/
WORKDIR /opt/venv/
COPY media_tagging/ ./media_tagging/
COPY pyproject.toml .

RUN chown -R appuser:appuser /opt/venv/media_tagging
EXPOSE 8000
ENV PYTHONPATH="/opt/venv"
USER appuser
CMD ["uvicorn", "media_tagging.entrypoints.server:app", "--host", "0.0.0.0"]
