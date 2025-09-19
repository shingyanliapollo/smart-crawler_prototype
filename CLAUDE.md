# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart Crawl is a batch processing system for fetching web content using the Firecrawl API. It processes URLs from CSV files and saves the content as Markdown files.

## Key Commands

### Development Setup
```bash
# Initial setup (only needed once)
make setup

# Build Docker images
make build

# Start containers
make up
```

### Running the Fetch Content Job
```bash
# Run fetch_content job using Docker
docker-compose run --rm batch python -m src.batch.main fetch_content

# Alternative using Makefile (Note: Makefile needs updating for fetch_content)
make run-batch JOB_NAME=fetch_content
```

### Development Commands
```bash
# View available jobs
docker-compose run --rm batch python -m src.batch.main

# Connect to container shell
make shell

# View logs
make logs

# Run tests
make test

# Code quality checks
make lint
```

## Architecture Overview

### Batch Job Framework
The system uses a base class pattern (`src/batch/base.py`) that provides:
- Automatic retry logic (3 attempts with exponential backoff)
- Structured logging with timing metrics
- Pre/post execution hooks
- Error handling with `on_error` hook

All batch jobs inherit from `BaseBatchJob` and must implement:
- `execute()`: Main job logic
- Optional: `before_execute()`, `after_execute()`, `on_error()`

### FetchContentJob Workflow
1. **Input**: Reads URLs from CSV files in `input/` directory
2. **Processing**: Calls Firecrawl API for each URL
3. **Output**: Saves Markdown content to `output/YYYYMMDD_HHMMSS/` directory
4. **Files**: Named as `{sequence}_{timestamp}.md` (e.g., `001_20250319_143022.md`)

### Critical Configuration
- **Firecrawl API Key**: Must be set in `.env` file as `FIRECRAWL_API_KEY`
- **Volume Mounts**: Docker mounts `input/` and `output/` directories for data persistence

### Job Registration
New jobs are registered in `src/batch/main.py`:
```python
AVAILABLE_JOBS = {
    "fetch_content": FetchContentJob,
    # Add new jobs here
}
```

## Important Implementation Details

### Firecrawl API Integration
- Endpoint: `https://api.firecrawl.dev/v1/scrape`
- Request format: `{"url": "...", "formats": ["markdown"], "onlyMainContent": true}`
- Authentication: Bearer token in header

### Error Handling
- Individual URL failures don't stop the batch
- Failed URLs are logged but processing continues
- Statistics (success/failure counts) are tracked and reported

### Current Implementation Status
Based on specs in `specs/` directory:
- ✅ URLコンテンツの取得 (URL content fetching) - Implemented
- ⏳ フィルタリング (Content filtering) - Not yet implemented
- ⏳ データ変換 (Data transformation) - Not yet implemented

## Testing Considerations
When adding tests, note that the project uses:
- pytest for testing framework
- structlog for logging (use `caplog` fixture to test log output)
- Docker environment for consistent testing