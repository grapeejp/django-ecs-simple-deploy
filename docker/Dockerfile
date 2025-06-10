FROM --platform=linux/amd64 python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

COPY app/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# セキュリティのためにnon-rootユーザーを作成
RUN addgroup --system appgroup && \
    adduser --system --group appuser

# 必要なパッケージをインストール
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

COPY ./app/ .

# 静的ファイル用のディレクトリを作成
RUN mkdir -p /app/staticfiles /app/mediafiles && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# マイグレーション実行とGunicorn起動をまとめたスクリプト作成
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'echo "データベースマイグレーション実行中..."' >> /app/start.sh && \
    echo 'python manage.py migrate --noinput' >> /app/start.sh && \
    echo 'echo "静的ファイル収集中..."' >> /app/start.sh && \
    echo 'python manage.py collectstatic --noinput' >> /app/start.sh && \
    echo 'echo "デモユーザー作成中..."' >> /app/start.sh && \
    echo 'python manage.py create_demo_users' >> /app/start.sh && \
    echo 'echo "Gunicornサーバー起動中..."' >> /app/start.sh && \
    echo 'exec gunicorn --bind 0.0.0.0:8000 --timeout 180 --workers 2 config.wsgi:application' >> /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"] 