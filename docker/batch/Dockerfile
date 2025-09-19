# マルチステージビルドでイメージサイズを最適化
FROM python:3.11-slim as builder

# 作業ディレクトリ
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存パッケージのインストール
COPY requirements/base.txt requirements/prod.txt requirements/dev.txt /app/requirements/
RUN pip install --no-cache-dir --user -r requirements/dev.txt

# 本番用イメージ
FROM python:3.11-slim

# 環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# 非rootユーザーの作成
RUN useradd -m -u 1000 appuser

# 作業ディレクトリ
WORKDIR /app

# builderステージから依存パッケージをコピー
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# アプリケーションコードをコピー
COPY --chown=appuser:appuser ./src /app/src
COPY --chown=appuser:appuser ./scripts /app/scripts

# 非rootユーザーに切り替え
USER appuser

# デフォルトコマンド
CMD ["python", "-m", "src.batch.main"]