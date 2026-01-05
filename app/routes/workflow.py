import csv
import logging
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter
from pydantic import BaseModel
from personal_prompt_temporary import PERSONAL_PROMPT_TEMPORARY
from app.services.toggl_service import get_toggl_track_activity_logs
from app.models.analysis import (
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    ResponseMode,
)
from app.routes.analysis import create_analysis

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

    # Step 2: Create analysis for each prompt
    logger.info(
        f"Step 2: Creating analysis for {len(PERSONAL_PROMPT_TEMPORARY)} metrics..."
    )
    analysis_responses = []
    for i, prompt in enumerate(PERSONAL_PROMPT_TEMPORARY, 1):
        logger.info(f"Processing metric {i}/{len(PERSONAL_PROMPT_TEMPORARY)}")
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
