FROM python:3.11.8-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=1
COPY requirements.txt .
RUN uv pip install --require-hashes -r requirements.txt
ENV GOOGLE_APPLICATION_CREDENTIALS /app/service_account.json
WORKDIR /app/data/
ENTRYPOINT ["filonov"]
