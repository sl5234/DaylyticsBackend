import csv
import logging
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter
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


def _get_bed_time_activity_logs_from_next_date(start_date: str) -> List[TogglTimeEntry]:
    """
    Bed time activity log for current date is defined as follows:
    1. The activity log occurred between 12:00 (noon) of the current date -12:00 (noon) of the next date.
    2. The activity log has tag "bed_time" or "sleep".

    Get bed_time activity logs from the next date that occurred between 00:00-12:00 (noon).

    Args:
        start_date: Start date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        List of TogglTimeEntry objects with bed_time or sleep tags from next date (00:00-12:00)
    """
    next_date = get_next_date(start_date)
    next_date_end = get_next_date(next_date)

    activity_logs = get_toggl_track_activity_logs(next_date, next_date_end)
    bed_time_logs = _filter_activity_log_with_bed_time_tag(activity_logs)
    filtered_logs = _filter_activity_log_started_between_00_00_12_00(
        bed_time_logs, next_date
    )

    return filtered_logs


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

    # Step 1: Retrieve activity logs
    logger.info("Step 1: Retrieving activity logs from Toggl Track...")
    activity_logs = get_toggl_track_activity_logs(request.start_date, request.end_date)
    logger.info(f"Retrieved {len(activity_logs)} activity logs")

    # Step 1.5: Get bed_time activity logs from next date (00:00-12:00)
    logger.info("Step 1.5: Retrieving bed_time activity logs from next date...")
    next_date_bed_time_logs = _get_bed_time_activity_logs_from_next_date(
        request.start_date
    )
    logger.info(
        f"Retrieved {len(next_date_bed_time_logs)} bed_time logs from next date"
    )
    activity_logs.extend(next_date_bed_time_logs)

    # Step 2: Create analysis for each prompt
    personal_prompts = get_personal_prompt_temporary(request.start_date)
    logger.info(f"Step 2: Creating analysis for {len(personal_prompts)} metrics...")
    analysis_responses = []
    for i, prompt in enumerate(personal_prompts, 1):
        logger.info(f"Processing metric {i}/{len(personal_prompts)}")
        analysis_request = CreateAnalysisRequest(
            prompt=prompt,
            response_mode=ResponseMode.METRIC,
            activity_logs=activity_logs,
        )
        analysis_response = create_analysis(analysis_request)
        analysis_responses.append(analysis_response)
        logger.info(f"Analysis {i} created with RID: {analysis_response.analysis_rid}")

    # Step 3: Write all metrics to CSV file
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
