#!/usr/bin/env python3
"""
Batch export demo dataset to JSONL.

Usage:
    # Run as module from project root
    python -m src.server.features.demo_analyzer.export_dataset --input-dir /tmp_demos --output-jsonl dataset.jsonl

    # Or run directly from project root
    python src/server/features/demo_analyzer/export_dataset.py --input-dir /tmp_demos --output-jsonl dataset.jsonl

This script processes all .dem files in the input directory, analyzes them using DemoAnalyzer,
builds training samples, and appends them to the specified JSONL file.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.server.features.demo_analyzer.service import DemoAnalyzer
from src.server.features.demo_analyzer.dataset import build_training_sample_from_demo, append_samples_to_jsonl
from src.server.features.demo_analyzer.models import DemoTrainingSample


class MockUploadFile:
    """Mock UploadFile for CLI usage that mimics FastAPI's UploadFile interface."""

    def __init__(self, filename: str, file_data: bytes):
        self.filename = filename
        self._data = file_data
        self._position = 0
        self.content_type = "application/octet-stream"

    async def read(self, size: int = -1) -> bytes:
        """Read data from file. If size is -1, read all remaining data."""
        if size == -1:
            result = self._data[self._position:]
            self._position = len(self._data)
            return result
        else:
            result = self._data[self._position:self._position + size]
            self._position += len(result)
            return result

    async def close(self):
        pass


async def process_demo_file(demo_path: Path, analyzer: DemoAnalyzer, source: str) -> Optional[DemoTrainingSample]:
    """Process a single .dem file and return training sample."""
    print(f"Processing {demo_path}...")

    try:
        # Read file in chunks to avoid loading entire large file into memory
        with open(demo_path, 'rb') as f:
            file_data = f.read()

        upload_file = MockUploadFile(demo_path.name, file_data)

        # Analyze demo (this calls all the AI services)
        analysis = await analyzer.analyze_demo(upload_file, language="ru")

        # Build training sample
        sample = build_training_sample_from_demo(analysis, source=source)

        # Safe access to rounds count
        rounds_count = 0
        if sample.input and hasattr(sample.input, 'rounds') and sample.input.rounds:
            rounds_count = len(sample.input.rounds)
        print(f"  -> Generated sample with {rounds_count} rounds")
        return sample

    except Exception as e:
        print(f"  -> Error processing {demo_path}: {e}")
        logging.exception("Full traceback:")
        return None


async def main():
    parser = argparse.ArgumentParser(description="Export demo dataset to JSONL")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing .dem files"
    )
    parser.add_argument(
        "--output-jsonl",
        type=str,
        required=True,
        help="Output JSONL file path"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="demo_analyzer_batch_export",
        help="Source identifier for training samples (default: demo_analyzer_batch_export)"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of files to process (for testing)"
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_jsonl = Path(args.output_jsonl)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory {input_dir} does not exist or is not a directory")
        sys.exit(1)

    demo_files = list(input_dir.glob("*.dem"))
    if not demo_files:
        print(f"No .dem files found in {input_dir}")
        sys.exit(1)

    if args.max_files:
        demo_files = demo_files[:args.max_files]
        print(f"Limited to {len(demo_files)} files for testing")

    print(f"Found {len(demo_files)} .dem files")
    print(f"Output will be written to {output_jsonl}")

    # Initialize analyzer (loads AI services)
    print("Initializing DemoAnalyzer...")
    analyzer = DemoAnalyzer()

    samples: list[Any] = []
    processed = 0
    errors = 0

    for demo_path in demo_files:
        sample = await process_demo_file(demo_path, analyzer, args.source)
        if sample:
            samples.append(sample)
            processed += 1
        else:
            errors += 1

        # Periodically save to avoid memory issues
        if len(samples) >= 10:
            append_samples_to_jsonl(samples, output_jsonl)
            print(f"Saved {len(samples)} samples to {output_jsonl}")
            samples = []

    # Save remaining samples
    if samples:
        append_samples_to_jsonl(samples, output_jsonl)
        print(f"Saved final {len(samples)} samples to {output_jsonl}")

    print(f"\nDone! Processed: {processed}, Errors: {errors}")
    print(f"Total samples in {output_jsonl}: check with 'wc -l {output_jsonl}'")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Check if running in project root
    if not Path('pyproject.toml').exists() and not Path('src').exists():
        print("Warning: Script should be run from project root directory")
        print(f"Current directory: {Path.cwd()}")

    asyncio.run(main())
