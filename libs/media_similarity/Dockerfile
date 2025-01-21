FROM python:3.11-slim-buster
ADD requirements.txt /tmp
RUN pip install --require-hashes -r /tmp/requirements.txt --no-deps
COPY app/ /app/
COPY tests /tests/
WORKDIR /app
