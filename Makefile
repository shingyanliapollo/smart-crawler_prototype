.PHONY: help setup build up down run-batch test lint clean logs shell restart status

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  make setup       - Initial setup (create venv and install dependencies)"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start Docker containers"
	@echo "  make down        - Stop Docker containers"
	@echo "  make restart     - Restart Docker containers"
	@echo "  make run-batch   - Run batch job (JOB_NAME=<job_name>)"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run code quality checks"
	@echo "  make clean       - Clean up cache and temp files"
	@echo "  make logs        - Show container logs"
	@echo "  make shell       - Connect to container shell"
	@echo "  make status      - Show container status"

# 初回セットアップ
setup:
	@echo "Setting up Python virtual environment..."
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements/dev.txt
	@echo "Creating .env file from template..."
	cp -n .env.example .env || true
	@echo "Setup completed! Activate venv with: source venv/bin/activate"

# Dockerイメージビルド
build:
	docker-compose build

# コンテナ起動
up:
	docker-compose up -d
	@echo "Containers started successfully!"
	@make status

# コンテナ停止
down:
	docker-compose down

# コンテナ再起動
restart:
	@make down
	@make up

# バッチ処理実行
run-batch:
	@if [ -z "$(JOB_NAME)" ]; then \
		echo "Usage: make run-batch JOB_NAME=<job_name>"; \
		echo "Available jobs:"; \
		echo "  - sample_job"; \
		exit 1; \
	fi
	docker-compose run --rm batch python -m src.batch.jobs.$(JOB_NAME)

# テスト実行
test:
	docker-compose run --rm batch pytest tests/ -v

# コード品質チェック
lint:
	docker-compose run --rm batch sh -c "black --check src/ tests/ && flake8 src/ tests/ && mypy src/"

# ローカルでのlint (venv使用)
lint-local:
	@if [ ! -d "venv" ]; then \
		echo "Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	./venv/bin/black --check src/ tests/
	./venv/bin/flake8 src/ tests/
	./venv/bin/mypy src/

# クリーンアップ
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleanup completed!"

# ログ表示
logs:
	docker-compose logs -f

# コンテナ内シェル接続
shell:
	docker-compose run --rm batch /bin/bash

# コンテナステータス確認
status:
	@docker-compose ps