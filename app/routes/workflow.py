import csv
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from personal_prompt_temporary import get_personal_prompt_temporary
from app.services.toggl_service import get_toggl_track_activity_logs
from app.models.analysis import (
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    ResponseMode,
)
from app.models.toggl import TogglTimeEntry
from app.routes.analysis import create_analysis
from app.utils.general_util import get_next_date

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["workflow"])

# Fixed column order (metric titles as they appear from the API)
CSV_COLUMN_ORDER = [
    "WakeUpTimePerDay",
    "BedTimePerDay",
    "TotalWorkoutTimePerDay",
    "TotalFamilyTimePerDay",
    "TotalResearchTimePerDay",
    "TotalReadingTimePerDay",
    "TotalAmazonTimePerDay",
    "TotalAppBuildingTimePerDay",
    "TotalFinanceTimePerDay",
    "TotalLanguageStudyTimePerDay",
    "UnrecordedTimePerDay",
    "TotalWorkTimePerDay",
    "TotalDatingTimePerDay",
]


def _write_metrics_to_csv(
    csv_path: Path, analysis_responses: List[CreateAnalysisResponse]
) -> None:
    """
    Write all metrics from analysis responses to CSV file.

    Builds data structure in memory and writes CSV file once.

    Args:
        csv_path: Path to the CSV file
        analysis_responses: List of CreateAnalysisResponse objects
    """
    rows_by_date: Dict[str, Dict[str, str]] = {}
    all_column_names: set = {"Day"}

    # Build data structure in memory
    for analysis_response in analysis_responses:
        if analysis_response.raw_output is None:
            continue
        metrics = analysis_response.raw_output
        for metric in metrics:
            # Format date as MM/DD/YYYY
            date_str = metric.date.strftime("%m/%d/%Y")

            # Get or create row for this date
            if date_str not in rows_by_date:
                rows_by_date[date_str] = {"Day": date_str}

            # Use metric title directly as column name
            column_name = metric.title
            all_column_names.add(column_name)

            # Set the metric value (always in minutes)
            rows_by_date[date_str][column_name] = str(metric.value)

    # Build final column order: Day first, then CSV_COLUMN_ORDER (excluding Day), then any others
    final_columns = ["Day"]
    for col in CSV_COLUMN_ORDER:
        if col != "Day" and col in all_column_names:
            final_columns.append(col)

    # Add any remaining columns not in CSV_COLUMN_ORDER
    for col in sorted(all_column_names):
        if col not in final_columns:
            final_columns.append(col)

    # Ensure all rows have all columns
    for row in rows_by_date.values():
        for col in final_columns:
            if col not in row:
                row[col] = ""

    # Write CSV file once with fixed column order
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=final_columns)
        writer.writeheader()
        for date_key in rows_by_date.keys():
            writer.writerow(rows_by_date[date_key])

    logger.info(
        f"Wrote {len(rows_by_date)} rows with {len(final_columns)} columns to CSV"
    )


def _filter_activity_log_with_bed_time_tag(
    activity_logs: List[TogglTimeEntry],
) -> List[TogglTimeEntry]:
    """
    Filter activity logs that have "bed_time" or "sleep" tags.

    Args:
        activity_logs: List of TogglTimeEntry objects

    Returns:
        List of TogglTimeEntry objects with bed_time or sleep tags
    """
    filtered_logs = []
    for log in activity_logs:
        has_bed_time_tag = "bed_time" in log.tags
        has_sleep_tag = "sleep" in log.tags
        if has_bed_time_tag or has_sleep_tag:
            filtered_logs.append(log)
    return filtered_logs


def _filter_activity_log_started_between_00_00_12_00(
    activity_logs: List[TogglTimeEntry], next_date: str
) -> List[TogglTimeEntry]:
    """
    Filter bed_time or sleep activity logs that occurred between 00:00 and 12:00 (noon) of next_date.

    Args:
        activity_logs: List of TogglTimeEntry objects (should already be filtered to only include bed_time or sleep logs)
        next_date: Next date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        List of filtered TogglTimeEntry objects with bed_time or sleep tags that start between 00:00-12:00 of next_date
    """
    filtered_logs = []
    seattle_tz = ZoneInfo("America/Los_Angeles")
    utc_tz = ZoneInfo("UTC")

    next_date_normalized = next_date.replace("Z", "+00:00")
    next_date_parsed = datetime.fromisoformat(next_date_normalized)
    if next_date_parsed.tzinfo is None:
        next_date_utc = next_date_parsed.replace(tzinfo=utc_tz)
    else:
        next_date_utc = next_date_parsed.astimezone(utc_tz)
    next_date_seattle = next_date_utc.astimezone(seattle_tz)
    next_date_str = next_date_seattle.strftime("%Y-%m-%d")

    next_date_start = next_date_seattle.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    next_date_noon = next_date_seattle.replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    for log in activity_logs:
        log_start_utc = log.start
        if log_start_utc.tzinfo is None:
            log_start_utc = log_start_utc.replace(tzinfo=utc_tz)
        else:
            log_start_utc = log_start_utc.astimezone(utc_tz)
        log_start_seattle = log_start_utc.astimezone(seattle_tz)
        log_start_date_str = log_start_seattle.strftime("%Y-%m-%d")

        if log_start_date_str == next_date_str:
            if next_date_start <= log_start_seattle < next_date_noon:
                filtered_logs.append(log)

    return filtered_logs


def _get_bed_time_logs_for_next_date(
    activity_logs: List[TogglTimeEntry], next_date: str
) -> List[TogglTimeEntry]:
    """
    Get bed_time activity logs from pre-fetched data for a specific next date (00:00-12:00).

    Bed time activity log for a date is defined as:
    1. Has tag "bed_time" or "sleep"
    2. Started between 00:00 and 12:00 (noon) of the next date

    Args:
        activity_logs: List of all pre-fetched TogglTimeEntry objects
        next_date: The next date as ISO-8601 datetime string

    Returns:
        List of TogglTimeEntry objects with bed_time/sleep tags from next date (00:00-12:00)
    """
    bed_time_logs = _filter_activity_log_with_bed_time_tag(activity_logs)
    filtered_logs = _filter_activity_log_started_between_00_00_12_00(
        bed_time_logs, next_date
    )
    return filtered_logs


def _filter_activity_logs_for_date(
    activity_logs: List[TogglTimeEntry], target_date: str
) -> List[TogglTimeEntry]:
    """
    Filter activity logs that belong to a specific date.

    A log belongs to the target date if:
    1. It started on the target date, OR
    2. It started on the previous date and ended on the target date

    Args:
        activity_logs: List of TogglTimeEntry objects
        target_date: Target date as ISO-8601 datetime string

    Returns:
        List of TogglTimeEntry objects that belong to the target date
    """
    filtered_logs = []
    seattle_tz = ZoneInfo("America/Los_Angeles")
    utc_tz = ZoneInfo("UTC")

    # Parse target date and get date string in Seattle timezone
    target_date_normalized = target_date.replace("Z", "+00:00")
    target_dt = datetime.fromisoformat(target_date_normalized)
    if target_dt.tzinfo is None:
        target_dt = target_dt.replace(tzinfo=utc_tz)
    target_dt_seattle = target_dt.astimezone(seattle_tz)
    target_date_str = target_dt_seattle.strftime("%Y-%m-%d")

    # Calculate previous date string
    prev_dt_seattle = target_dt_seattle - timedelta(days=1)
    prev_date_str = prev_dt_seattle.strftime("%Y-%m-%d")

    for log in activity_logs:
        # Get log start date in Seattle timezone
        log_start_utc = log.start
        if log_start_utc.tzinfo is None:
            log_start_utc = log_start_utc.replace(tzinfo=utc_tz)
        else:
            log_start_utc = log_start_utc.astimezone(utc_tz)
        log_start_seattle = log_start_utc.astimezone(seattle_tz)
        log_start_date_str = log_start_seattle.strftime("%Y-%m-%d")

        # Case 1: Log started on target date
        if log_start_date_str == target_date_str:
            filtered_logs.append(log)
            continue

        # Case 2: Log started on previous date and ended on target date
        if log_start_date_str == prev_date_str and log.stop is not None:
            log_end_utc = log.stop
            if log_end_utc.tzinfo is None:
                log_end_utc = log_end_utc.replace(tzinfo=utc_tz)
            else:
                log_end_utc = log_end_utc.astimezone(utc_tz)
            log_end_seattle = log_end_utc.astimezone(seattle_tz)
            log_end_date_str = log_end_seattle.strftime("%Y-%m-%d")

            if log_end_date_str == target_date_str:
                filtered_logs.append(log)

    return filtered_logs


def _get_dates_in_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate a list of dates from start_date to end_date (inclusive).

    Args:
        start_date: Start date as ISO-8601 datetime string
        end_date: End date as ISO-8601 datetime string

    Returns:
        List of ISO-8601 datetime strings for each day in the range
    """
    dates = []
    current_date = start_date
    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    while True:
        current_dt = datetime.fromisoformat(current_date.replace("Z", "+00:00"))
        if current_dt > end_dt:
            break
        dates.append(current_date)
        current_date = get_next_date(current_date)

    return dates


class StartWorkflowRequest(BaseModel):
    """Request model for StartWorkflow endpoint."""

    start_date: str
    end_date: str


class StartWorkflowResponse(BaseModel):
    """Response model for StartWorkflow endpoint."""

    analysis_rid: str
    output_config: dict


# This API is temporary.  In the future, we want to deprecate it.
# Instead, we want to use a combination of Planner Agent,
# TogglTrack MCP server, and Analyzer Agent (i.e. CreateAnalysis API).
# In that world, the MCP client (e.g. Claude CLI or Kiro CLI) will be
# the orchestrator of the workflow.
@router.post("/", response_model=StartWorkflowResponse)
def start_workflow(request: StartWorkflowRequest) -> StartWorkflowResponse:
    """
    Start workflow to retrieve activity logs and create analysis.

    Orchestrates the full workflow:
    1. Retrieves activity logs from Toggl Track API
    2. Creates analysis from the retrieved logs

    Args:
        request: StartWorkflowRequest containing start_date and end_date

    Returns:
        StartWorkflowResponse containing analysis results
    """
    logger.info(f"Starting workflow from {request.start_date} to {request.end_date}")

    # Validate date range (max 5 days)
    start_dt = datetime.fromisoformat(request.start_date.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(request.end_date.replace("Z", "+00:00"))
    date_diff = (end_dt - start_dt).days
    if date_diff > 20:
        raise HTTPException(
            status_code=400,
            detail=f"Date range exceeds maximum of 20 days. Got {date_diff} days.",
        )

    # Step 1: Retrieve activity logs (fetch from start_date - 1 day to end_date + 1 day)
    # Extra day at start: for logs that started prev day and ended on start_date
    # Extra day at end: for bed_time logs from the day after end_date
    logger.info("Step 1: Retrieving activity logs from Toggl Track...")
    start_date_minus_one = (start_dt - timedelta(days=1)).isoformat()
    end_date_plus_one = get_next_date(request.end_date)
    all_activity_logs = get_toggl_track_activity_logs(
        start_date_minus_one, end_date_plus_one
    )
    logger.info(f"Retrieved {len(all_activity_logs)} activity logs")

    # Step 2: Build all analysis requests for all dates
    dates_in_range = _get_dates_in_range(request.start_date, request.end_date)
    logger.info(f"Step 2: Building requests for {len(dates_in_range)} dates...")
    all_analysis_requests = []

    for date_idx, current_date in enumerate(dates_in_range, 1):
        logger.info(f"Building requests for date {date_idx}/{len(dates_in_range)}: {current_date}")

        # Filter activity logs for this date
        date_activity_logs = _filter_activity_logs_for_date(
            all_activity_logs, current_date
        )
        logger.info(f"  Found {len(date_activity_logs)} activity logs for this date")

        # Get bed_time logs from next date (00:00-12:00)
        next_date = get_next_date(current_date)
        bed_time_logs = _get_bed_time_logs_for_next_date(all_activity_logs, next_date)
        logger.info(f"  Found {len(bed_time_logs)} bed_time logs from next date")

        # Combine activity logs with bed_time logs
        combined_logs = date_activity_logs + bed_time_logs

        # Get personal prompts and build requests for this date
        personal_prompts = get_personal_prompt_temporary(current_date)
        logger.info(f"  Building {len(personal_prompts)} requests for this date")

        for prompt in personal_prompts:
            all_analysis_requests.append(
                CreateAnalysisRequest(
                    prompt=prompt,
                    response_mode=ResponseMode.METRIC,
                    activity_logs=combined_logs,
                )
            )

    # Step 3: Execute all requests in parallel
    logger.info(f"Step 3: Executing {len(all_analysis_requests)} analysis requests in parallel...")
    with ThreadPoolExecutor(max_workers=len(all_analysis_requests)) as executor:
        analysis_responses = list(executor.map(create_analysis, all_analysis_requests))
    logger.info(f"Completed {len(analysis_responses)} analyses")

    # Step 4: Write all metrics to CSV file
    desktop_path = Path.home() / "Desktop"
    # Extract date part from ISO-8601 datetime strings
    start_date_part = (
        request.start_date.split("T")[0]
        if "T" in request.start_date
        else request.start_date
    )
    end_date_part = (
        request.end_date.split("T")[0] if "T" in request.end_date else request.end_date
    )
    csv_filename = f"AnalysisOutput{start_date_part}{end_date_part}.csv"
    csv_path = desktop_path / csv_filename

    logger.info(f"Writing all metrics to CSV file at {csv_path}")
    _write_metrics_to_csv(csv_path, analysis_responses)
    logger.info(f"Completed workflow. CSV file saved at {csv_path}")

    # Return any dummy value.
    return StartWorkflowResponse(analysis_rid="foo", output_config={})
