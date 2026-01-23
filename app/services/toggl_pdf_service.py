from typing import Dict, Any, List, Optional
import logging
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pdfplumber
from app.models.toggl import TogglTimeEntry
from app.services.helpers.toggl_service_helper import deserialize_time_entries

logger = logging.getLogger(__name__)


def _parse_duration_to_seconds(duration_str: str) -> int:
    """
    Parse duration string (H:MM:SS or -) to seconds.

    Args:
        duration_str: Duration string like "8:32:06" or "-"

    Returns:
        Duration in seconds, 0 for "-" or empty strings
    """
    if not duration_str or duration_str.strip() == "-":
        return 0

    parts = duration_str.strip().split(":")
    if len(parts) == 3:
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes, seconds = int(parts[0]), int(parts[1])
        return minutes * 60 + seconds
    return 0


def _parse_time_date_column(
    time_date_str: str,
) -> tuple[str, str, str, Optional[str]]:
    """
    Parse the TIME | DATE column from Toggl PDF.

    Args:
        time_date_str: String like "21:42 - 06:15\\n10/26/2025 - 10/27/2025"
                       or "19:58 - 20:14\\n10/26/2025"

    Returns:
        Tuple of (start_time, end_time, start_date, end_date)
        end_date is None if entry doesn't span midnight
    """
    lines = time_date_str.strip().split("\n")
    time_line = lines[0].strip()
    date_line = lines[1].strip() if len(lines) > 1 else ""

    # Parse time range: "21:42 - 06:15"
    time_match = re.match(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", time_line)
    if not time_match:
        raise ValueError(f"Could not parse time from: {time_line}")
    start_time = time_match.group(1)
    end_time = time_match.group(2)

    # Parse date(s): "10/26/2025" or "10/26/2025 - 10/27/2025"
    date_match = re.match(
        r"(\d{1,2}/\d{1,2}/\d{4})(?:\s*-\s*(\d{1,2}/\d{1,2}/\d{4}))?", date_line
    )
    if not date_match:
        raise ValueError(f"Could not parse date from: {date_line}")
    start_date = date_match.group(1)
    end_date = date_match.group(2)  # None if no second date

    return start_time, end_time, start_date, end_date


def _build_iso_datetime(date_str: str, time_str: str) -> str:
    """
    Build ISO-8601 datetime string from date and time.

    Args:
        date_str: Date like "10/26/2025" (MM/DD/YYYY)
        time_str: Time like "21:42" (HH:MM)

    Returns:
        ISO-8601 datetime string with Seattle timezone (handles DST)
    """
    seattle_tz = ZoneInfo("America/Los_Angeles")

    # Parse MM/DD/YYYY
    month, day, year = date_str.split("/")

    # Parse HH:MM
    hour, minute = time_str.split(":")

    # Create datetime in Seattle timezone (handles DST automatically)
    dt = datetime(
        int(year), int(month), int(day), int(hour), int(minute), 0, tzinfo=seattle_tz
    )

    return dt.isoformat()


def _get_time_entries_from_pdf(local_path: Path) -> List[Dict[str, Any]]:
    """
    Extract time entries from a Toggl Track PDF report.

    Parses PDF tables and extracts time entry data including description,
    duration, tags, and start/stop times.

    Args:
        local_path: Path to the Toggl Track PDF file

    Returns:
        List of raw time entry dictionaries ready for deserialization
    """
    logger.info(f"Extracting time entries from PDF: {local_path}")

    raw_entries: List[Dict[str, Any]] = []

    with pdfplumber.open(local_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables()
            logger.debug(f"Page {page_num}: found {len(tables)} tables")

            for table in tables:
                if not table:
                    continue

                # Skip header row, process data rows
                for row in table[1:]:  # Skip header
                    if not row or len(row) < 6:
                        continue

                    # Columns: DESCRIPTION, DURATION, MEMBER, PROJECT, TAGS, TIME | DATE
                    description = row[0] or ""
                    duration_str = row[1] or "-"
                    # row[2] is MEMBER (ignored)
                    # row[3] is PROJECT (ignored)
                    tags_str = row[4] or ""
                    time_date_str = row[5] or ""

                    # Skip empty rows or header-like rows
                    if not description or description == "DESCRIPTION":
                        continue

                    try:
                        # Parse time/date
                        start_time, end_time, start_date, end_date = (
                            _parse_time_date_column(time_date_str)
                        )

                        # Use end_date for stop time if entry spans midnight
                        stop_date = end_date if end_date else start_date

                        # Build ISO datetime strings
                        start_iso = _build_iso_datetime(start_date, start_time)
                        stop_iso = _build_iso_datetime(stop_date, end_time)

                        # Parse duration
                        duration_seconds = _parse_duration_to_seconds(duration_str)

                        # Build raw entry dict
                        raw_entry = {
                            "description": description.strip(),
                            "tags": [tags_str.strip()] if tags_str.strip() else [],
                            "start": start_iso,
                            "stop": stop_iso,
                            "duration": duration_seconds,
                        }
                        raw_entries.append(raw_entry)
                        logger.debug(f"Parsed entry: {description} - {tags_str}")

                    except (ValueError, IndexError) as e:
                        logger.warning(
                            f"Could not parse row on page {page_num}: {row}. Error: {e}"
                        )
                        continue

    logger.info(f"Extracted {len(raw_entries)} time entries from PDF")
    return raw_entries


def _filter_entries_by_date_range(
    entries: List[TogglTimeEntry], start_date: str, end_date: str
) -> List[TogglTimeEntry]:
    """
    Filter entries that fall within the date range.

    An entry is included if:
    - Its start time falls within the range [start_date, end_date], OR
    - Its stop time falls within the range [start_date, end_date]

    Args:
        entries: List of TogglTimeEntry objects
        start_date: Start date as ISO-8601 datetime string
        end_date: End date as ISO-8601 datetime string

    Returns:
        List of filtered TogglTimeEntry objects
    """
    seattle_tz = ZoneInfo("America/Los_Angeles")
    utc_tz = ZoneInfo("UTC")

    # Parse start_date
    start_normalized = start_date.replace("Z", "+00:00")
    start_dt = datetime.fromisoformat(start_normalized)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=utc_tz)
    start_dt_seattle = start_dt.astimezone(seattle_tz)

    # Parse end_date
    end_normalized = end_date.replace("Z", "+00:00")
    end_dt = datetime.fromisoformat(end_normalized)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=utc_tz)
    end_dt_seattle = end_dt.astimezone(seattle_tz)

    filtered_entries = []
    for entry in entries:
        # Get entry start time in Seattle timezone
        entry_start = entry.start
        if entry_start.tzinfo is None:
            entry_start = entry_start.replace(tzinfo=utc_tz)
        entry_start_seattle = entry_start.astimezone(seattle_tz)

        # Get entry stop time in Seattle timezone
        entry_stop = entry.stop
        if entry_stop.tzinfo is None:
            entry_stop = entry_stop.replace(tzinfo=utc_tz)
        entry_stop_seattle = entry_stop.astimezone(seattle_tz)

        # Check if entry start OR stop falls within range
        start_in_range = start_dt_seattle <= entry_start_seattle <= end_dt_seattle
        stop_in_range = start_dt_seattle <= entry_stop_seattle <= end_dt_seattle
        if start_in_range or stop_in_range:
            filtered_entries.append(entry)

    return filtered_entries


def get_toggl_track_activity_logs_from_pdf(
    local_paths: List[str], start_date: str, end_date: str
) -> List[TogglTimeEntry]:
    """
    Get activity logs from multiple Toggl Track PDF reports for a date range.

    Extracts time entries from all PDFs, deserializes them into TogglTimeEntry objects,
    and filters to only include entries within the date range.

    Args:
        local_paths: List of paths to Toggl Track PDF files
        start_date: Start date as ISO-8601 datetime string
        end_date: End date as ISO-8601 datetime string

    Returns:
        List of TogglTimeEntry objects within the date range
    """
    logger.info(f"Getting activity logs from {len(local_paths)} PDF files")
    logger.info(f"Filtering for date range: {start_date} to {end_date}")

    all_entries: List[TogglTimeEntry] = []

    for local_path in local_paths:
        pdf_path = Path(local_path).expanduser()
        logger.info(f"Processing PDF: {pdf_path}")
        raw_entries = _get_time_entries_from_pdf(pdf_path)
        entries = deserialize_time_entries(raw_entries)
        all_entries.extend(entries)
        logger.info(f"  Extracted {len(entries)} entries from {pdf_path}")

    logger.info(f"Total entries from all PDFs: {len(all_entries)}")

    filtered_entries = _filter_entries_by_date_range(all_entries, start_date, end_date)
    logger.info(
        f"Filtered {len(all_entries)} entries down to {len(filtered_entries)} entries"
    )

    return filtered_entries
