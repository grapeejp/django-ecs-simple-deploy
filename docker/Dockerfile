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

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout", "180", "--workers", "2", "config.wsgi:application"] 