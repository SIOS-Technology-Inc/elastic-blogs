FROM python:3.13

WORKDIR /app

COPY ./requirements.txt ./

RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt

RUN groupadd -r appgroup && useradd -r -s /usr/sbin/nologin -g appgroup appuser

COPY --chown=appuser:appgroup ./ /app

USER appuser

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/bin/sh", "-c", "while :; do sleep 30; done"]
