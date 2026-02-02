FROM python:3.14-slim

ENV OTEL_SERVICE_NAME=my-python-script \
      OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
      OTEL_EXPORTER_OTLP_PROTOCOL=grpc \
      OTEL_TRACES_SAMPLER=always_on \
      OTEL_RESOURCE_ATTRIBUTES=service.name=edot,service.version=1.0.0,deployment.environment=dev

WORKDIR /app

# 必要なライブラリのインストール
RUN apt-get update && apt-get install -y vim wget

RUN pip install --upgrade pip
RUN pip install --no-cache-dir elastic-opentelemetry opentelemetry-distro opentelemetry-exporter-otlp

RUN groupadd appgroup && useradd -m -g appgroup appuser

COPY --chown=appuser:appgroup ./ /app

USER appuser

# コンテナがすぐに終了しないようにする
ENTRYPOINT ["/bin/sh", "-c", "while :; do sleep 30; done"]
