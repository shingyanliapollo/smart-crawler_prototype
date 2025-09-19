"""Fetch content from URLs using Firecrawl API."""

import os
import csv
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.batch.base import BaseBatchJob
from src.common.config import settings


class FetchContentJob(BaseBatchJob):
    """Job for fetching content from URLs using Firecrawl API."""

    def __init__(self):
        super().__init__("FetchContent")
        self.api_key: Optional[str] = None
        self.timestamp: Optional[str] = None
        self.output_dir: Optional[Path] = None
        self.urls: List[str] = []
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }

    def before_execute(self):
        """Preparation before job execution."""
        self.logger.info("Preparing FetchContent job...")

        # Check API key
        self.api_key = settings.firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        # Check input directory
        input_dir = Path("input")
        if not input_dir.exists():
            raise FileNotFoundError(
                f"Input directory not found: {input_dir}. "
                "Please create the 'input' directory and place your CSV file there."
            )

        # Find CSV file in input directory
        csv_files = list(input_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(
                "No CSV file found in 'input' directory. "
                "Please create a CSV file with a 'url' column."
            )

        # Use the first CSV file found
        csv_file = csv_files[0]
        self.logger.info(f"Using CSV file: {csv_file}")

        # Read URLs from CSV
        self.urls = self._read_urls_from_csv(csv_file)
        if not self.urls:
            raise ValueError("No valid URLs found in CSV file")

        self.stats["total"] = len(self.urls)
        self.logger.info(f"Found {self.stats['total']} URLs to process")

        # Create output directory with timestamp
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("output") / self.timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Output directory: {self.output_dir}")

        self.context["prepared"] = True

    def _read_urls_from_csv(self, csv_file: Path) -> List[str]:
        """Read URLs from CSV file."""
        urls = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if 'url' not in reader.fieldnames:
                    raise ValueError("CSV file must have a 'url' column")

                for row in reader:
                    url = row.get('url', '').strip()
                    if url and url.startswith('http'):
                        urls.append(url)
                    elif url:
                        self.logger.warning(f"Skipping invalid URL: {url}")

        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
            raise

        return urls

    def execute(self) -> Dict[str, Any]:
        """Main job logic."""
        self.logger.info("Executing FetchContent job...")

        for index, url in enumerate(self.urls, start=1):
            self.logger.info(f"Processing {index}/{self.stats['total']}: {url}")

            try:
                # Call Firecrawl API
                content = self._fetch_content(url)

                # Save to file
                file_name = f"{index:03d}_{self.timestamp}.md"
                file_path = self.output_dir / file_name

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Content from: {url}\n")
                    f.write(f"# Fetched at: {datetime.now().isoformat()}\n\n")
                    f.write(content)

                self.stats["success"] += 1
                self.logger.info(f"Successfully saved content to {file_name}")

            except Exception as e:
                self.stats["failed"] += 1
                self.logger.error(f"Failed to process {url}: {e}")
                continue

        # Calculate success rate
        success_rate = (
            (self.stats["success"] / self.stats["total"] * 100)
            if self.stats["total"] > 0 else 0
        )

        return {
            "total_urls": self.stats["total"],
            "successful": self.stats["success"],
            "failed": self.stats["failed"],
            "success_rate": success_rate,
            "output_directory": str(self.output_dir)
        }

    def _fetch_content(self, url: str) -> str:
        """Fetch content from URL using Firecrawl API."""
        api_url = "https://api.firecrawl.dev/v1/scrape"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Check if the response indicates success
                if data.get("success"):
                    # Get markdown content
                    if data.get("data") and data["data"].get("markdown"):
                        return data["data"]["markdown"]
                    else:
                        raise ValueError("No markdown content in response")
                else:
                    error_msg = data.get("error", "Unknown error")
                    raise ValueError(f"API returned error: {error_msg}")

            else:
                raise requests.HTTPError(
                    f"HTTP {response.status_code}: {response.text}"
                )

        except requests.RequestException as e:
            self.logger.error(f"Request error for {url}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {url}: {e}")
            raise

    def after_execute(self, result: Dict[str, Any]):
        """Cleanup after successful job execution."""
        self.logger.info("=" * 50)
        self.logger.info("FetchContent Job Summary:")
        self.logger.info(f"  Total URLs: {result['total_urls']}")
        self.logger.info(f"  Successful: {result['successful']}")
        self.logger.info(f"  Failed: {result['failed']}")
        self.logger.info(f"  Success Rate: {result['success_rate']:.1f}%")
        self.logger.info(f"  Output Directory: {result['output_directory']}")
        self.logger.info("=" * 50)

    def on_error(self, error: Exception):
        """Handle job failure."""
        self.logger.error(f"FetchContent job failed with error: {error}")
        if self.output_dir and self.output_dir.exists():
            self.logger.info(
                f"Partial results may be available in: {self.output_dir}"
            )