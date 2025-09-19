"""Main entry point for batch processing."""

import sys
import argparse
from typing import Optional
import structlog

from src.common.logging import setup_logging, get_logger
from src.batch.jobs.fetch_content_job import FetchContentJob


# Job registry
AVAILABLE_JOBS = {
    "fetch_content": FetchContentJob,
}


def main(job_name: Optional[str] = None):
    """Main function to run batch jobs.
    
    Args:
        job_name: Name of the job to run. If not provided, shows available jobs.
    """
    # Set up logging
    setup_logging()
    logger = get_logger(__name__)
    
    if not job_name:
        logger.info("No job specified. Available jobs:", jobs=list(AVAILABLE_JOBS.keys()))
        print("Available jobs:")
        for name in AVAILABLE_JOBS:
            print(f"  - {name}")
        return
    
    if job_name not in AVAILABLE_JOBS:
        logger.error(f"Unknown job: {job_name}")
        print(f"Error: Unknown job '{job_name}'")
        print("Available jobs:")
        for name in AVAILABLE_JOBS:
            print(f"  - {name}")
        sys.exit(1)
    
    # Get job class and create instance
    job_class = AVAILABLE_JOBS[job_name]
    job = job_class()
    
    # Run the job
    result = job.run()
    
    # Exit with appropriate code
    if result.get("status") == "success":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch jobs")
    parser.add_argument(
        "job",
        nargs="?",
        help="Name of the job to run",
        choices=list(AVAILABLE_JOBS.keys())
    )
    
    args = parser.parse_args()
    main(args.job)