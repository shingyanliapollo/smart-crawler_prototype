"""Filter content using LLM to extract event information."""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.batch.base import BaseBatchJob
from src.common.llm_service import ClaudeService


class FilterContentJob(BaseBatchJob):
    """Job for filtering content to extract event information using LLM."""

    def __init__(self):
        super().__init__("FilterContent")
        self.claude_service: Optional[ClaudeService] = None
        self.input_dir: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.timestamp: Optional[str] = None
        self.input_files: List[Path] = []
        self.stats = {
            "total_files": 0,
            "processed": 0,
            "events_found": 0,
            "failed": 0
        }

    def before_execute(self):
        """Preparation before job execution."""
        self.logger.info("Preparing FilterContent job...")

        # Initialize Claude service
        try:
            self.claude_service = ClaudeService()
        except Exception as e:
            raise ValueError(f"Failed to initialize Claude service: {e}")

        # Find the latest output directory from fetch_content
        output_base = Path("output")
        if not output_base.exists():
            raise FileNotFoundError(
                "Output directory not found. Please run fetch_content job first."
            )

        # Get the latest timestamped directory
        timestamp_dirs = [d for d in output_base.iterdir()
                         if d.is_dir() and d.name.replace('_', '').isdigit()]

        if not timestamp_dirs:
            raise FileNotFoundError(
                "No timestamped directories found in output. "
                "Please run fetch_content job first."
            )

        # Sort by timestamp and get the latest
        self.input_dir = sorted(timestamp_dirs, key=lambda d: d.name)[-1]
        self.logger.info(f"Using input directory: {self.input_dir}")

        # Find all markdown files in the input directory
        self.input_files = list(self.input_dir.glob("*.md"))
        if not self.input_files:
            raise FileNotFoundError(
                f"No markdown files found in {self.input_dir}"
            )

        self.stats["total_files"] = len(self.input_files)
        self.logger.info(f"Found {self.stats['total_files']} files to process")

        # Create output directory for filtered content
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_base / f"filtered_{self.timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Output directory: {self.output_dir}")

        self.context["prepared"] = True

    def execute(self) -> Dict[str, Any]:
        """Main job logic."""
        self.logger.info("Executing FilterContent job...")

        for index, file_path in enumerate(self.input_files, start=1):
            self.logger.info(
                f"Processing {index}/{self.stats['total_files']}: {file_path.name}"
            )

            try:
                # Read the content
                content = self._read_file_content(file_path)

                # Extract source URL from content if available
                source_url = self._extract_source_url(content)

                # Filter content using Claude
                filtered_result = self.claude_service.extract_event_info(
                    content, source_url
                )

                # Save the filtered result
                output_filename = f"filtered_{file_path.stem}_{self.timestamp}.json"
                output_path = self.output_dir / output_filename

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered_result, f, indent=2, ensure_ascii=False)

                self.stats["processed"] += 1

                # Check if events were found
                if filtered_result.get("has_event", False):
                    self.stats["events_found"] += 1
                    self.logger.info(
                        f"Events found in {file_path.name} - saved to {output_filename}"
                    )
                else:
                    self.logger.info(f"No events found in {file_path.name}")

            except Exception as e:
                self.stats["failed"] += 1
                self.logger.error(f"Failed to process {file_path.name}: {e}")

                # Save error information
                error_result = {
                    "has_event": False,
                    "error": str(e),
                    "source_file": str(file_path),
                    "timestamp": datetime.now().isoformat()
                }

                error_filename = f"error_{file_path.stem}_{self.timestamp}.json"
                error_path = self.output_dir / error_filename

                with open(error_path, 'w', encoding='utf-8') as f:
                    json.dump(error_result, f, indent=2, ensure_ascii=False)

                continue

        # Calculate success rate
        success_rate = (
            (self.stats["processed"] / self.stats["total_files"] * 100)
            if self.stats["total_files"] > 0 else 0
        )

        return {
            "total_files": self.stats["total_files"],
            "processed": self.stats["processed"],
            "events_found": self.stats["events_found"],
            "failed": self.stats["failed"],
            "success_rate": success_rate,
            "input_directory": str(self.input_dir),
            "output_directory": str(self.output_dir)
        }

    def _read_file_content(self, file_path: Path) -> str:
        """Read content from markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            raise

    def _extract_source_url(self, content: str) -> str:
        """Extract source URL from markdown content."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# Content from: '):
                return line.replace('# Content from: ', '').strip()
        return ""

    def after_execute(self, result: Dict[str, Any]):
        """Cleanup after successful job execution."""
        self.logger.info("=" * 50)
        self.logger.info("FilterContent Job Summary:")
        self.logger.info(f"  Total Files: {result['total_files']}")
        self.logger.info(f"  Processed: {result['processed']}")
        self.logger.info(f"  Events Found: {result['events_found']}")
        self.logger.info(f"  Failed: {result['failed']}")
        self.logger.info(f"  Success Rate: {result['success_rate']:.1f}%")
        self.logger.info(f"  Input Directory: {result['input_directory']}")
        self.logger.info(f"  Output Directory: {result['output_directory']}")
        self.logger.info("=" * 50)

    def on_error(self, error: Exception):
        """Handle job failure."""
        self.logger.error(f"FilterContent job failed with error: {error}")
        if self.output_dir and self.output_dir.exists():
            self.logger.info(
                f"Partial results may be available in: {self.output_dir}"
            )