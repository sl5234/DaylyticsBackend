"""
Last used on 2026-01-20.

This script is no longer used.
"""

import argparse
import csv
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _convert_timestamp(timestamp_format_a: Optional[int]) -> Optional[int]:
    """
    Convert timestamp from format A to format B.

    Format A: Time as number (e.g., 803 for 8:03 AM, 1105 for 11:05 AM, 2400 for 24:00, 2600 for 26:00)
    Format B: Minutes since 00:00 (e.g., 483 for 8:03 AM, 665 for 11:05 AM, 1440 for 24:00, 1560 for 26:00)

    Args:
        timestamp_format_a: Timestamp in format A (e.g., 803, 1105, 0803, 2400, 2600), or None

    Returns:
        Timestamp in format B (minutes since midnight), or None if input is None

    Raises:
        ValueError: If timestamp format is invalid
    """
    if timestamp_format_a is None:
        return None
    timestamp_str = str(timestamp_format_a).strip()
    if not timestamp_str or timestamp_str.lower() == "none":
        return None
    if len(timestamp_str) == 3:
        hours = int(timestamp_str[0])
        minutes = int(timestamp_str[1:])
    elif len(timestamp_str) == 4:
        hours = int(timestamp_str[:2])
        minutes = int(timestamp_str[2:])
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp_format_a}. Expected 3 or 4 digits.")
    if hours < 0:
        raise ValueError(f"Invalid hours: {hours}. Must be non-negative.")
    if minutes < 0 or minutes > 59:
        raise ValueError(f"Invalid minutes: {minutes}. Must be between 0 and 59.")
    minutes_since_midnight = hours * 60 + minutes
    return minutes_since_midnight


def _read_from_txt(input_path: Path) -> List[Optional[int]]:
    """
    Read timestamps from a text file (one per line).

    Args:
        input_path: Path to input text file

    Returns:
        List of timestamps (can contain None for empty lines)
    """
    timestamps: List[Optional[int]] = []
    with open(input_path, "r") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                timestamps.append(None)
                continue
            try:
                timestamp = int(line)
                timestamps.append(timestamp)
            except ValueError as e:
                logger.warning(f"Line {line_num}: Could not parse '{line}' as integer, skipping")
                timestamps.append(None)
    return timestamps


def _read_timestamps(input_path: Path) -> List[Optional[int]]:
    """
    Read timestamps from a text file.

    Args:
        input_path: Path to input text file

    Returns:
        List of timestamps (can contain None)

    Raises:
        ValueError: If file extension is not .txt
    """
    suffix = input_path.suffix.lower()
    if suffix != ".txt":
        raise ValueError(f"Unsupported file format: {suffix}. Only .txt files are supported.")
    return _read_from_txt(input_path)


def _publish_to_csv(timestamps: List[Optional[int]], output_path: Path) -> None:
    """
    Write array of timestamps to CSV file.

    Args:
        timestamps: Array of timestamp numbers to write (can contain None)
        output_path: Path to output CSV file
    """
    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp"])
        for timestamp in timestamps:
            writer.writerow([timestamp])


def convert_timestamps(timestamps_format_a: List[Optional[int]], output_path: Path) -> List[Optional[int]]:
    """
    Convert array of timestamps from format A to format B and write to CSV.

    Args:
        timestamps_format_a: Array of timestamps in format A (can contain None)
        output_path: Path to output CSV file

    Returns:
        Array of timestamps in format B (can contain None)
    """
    timestamps_format_b: List[Optional[int]] = []
    for ts in timestamps_format_a:
        try:
            converted = _convert_timestamp(ts)
            timestamps_format_b.append(converted)
        except ValueError as e:
            logger.error(f"Failed to convert timestamp {ts}: {e}")
            timestamps_format_b.append(None)
    _publish_to_csv(timestamps_format_b, output_path)
    return timestamps_format_b


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert timestamps from format A (e.g., 803 for 8:03 AM) to format B (minutes since midnight)"
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input text file containing timestamps (one per line)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output CSV file path (default: input_file with .csv extension)",
    )
    args = parser.parse_args()

    input_path = args.input_file
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if args.output is None:
        output_path = input_path.with_suffix(".csv")
    else:
        output_path = args.output

    logger.info(f"Reading timestamps from: {input_path}")
    timestamps_format_a = _read_timestamps(input_path)
    logger.info(f"Read {len(timestamps_format_a)} timestamps")

    logger.info(f"Converting timestamps...")
    timestamps_format_b = convert_timestamps(timestamps_format_a, output_path)
    valid_count = sum(1 for ts in timestamps_format_b)
    logger.info(f"Converted {valid_count} timestamps successfully")
    logger.info(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
