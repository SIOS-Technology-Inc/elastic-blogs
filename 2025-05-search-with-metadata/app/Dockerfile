FROM python:3.13

WORKDIR /app

COPY ./requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip==25.1.1
RUN pip install --no-cache-dir --requirement ./requirements.txt

# "appuser" という専用のグループとユーザーを作成（ログイン不要のシェル設定）
RUN groupadd -r appgroup && useradd -r -s /usr/sbin/nologin -g appgroup appuser

COPY --chown=appuser:appgroup ./ /app

# ユーザー権限を変更（アプリケーションディレクトリの所有者を "appuser" に設定）
RUN chown -R appuser:appgroup /app

USER appuser

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/bin/sh", "-c", "while :; do sleep 30; done"]
