import logging

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.toggl_service import get_toggl_track_activity_logs
from app.models.analysis import (
    CreateAnalysisRequest,
    ResponseMode,
)
from app.routes.analysis import create_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["workflow"])


class StartWorkflowRequest(BaseModel):
    """Request model for StartWorkflow endpoint."""

    user_prompt: str
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
        request: StartWorkflowRequest containing user_prompt, start_date, and end_date

    Returns:
        StartWorkflowResponse containing analysis results
    """
    logger.info(
        f"Starting workflow for prompt: {request.user_prompt} "
        f"from {request.start_date} to {request.end_date}"
    )

    # Step 1: Retrieve activity logs
    logger.info("Step 1: Retrieving activity logs from Toggl Track...")
    activity_logs = get_toggl_track_activity_logs(request.start_date, request.end_date)
    logger.info(f"Retrieved {len(activity_logs)} activity logs")

    # Step 2: Create analysis
    logger.info("Step 2: Creating analysis...")
    analysis_request = CreateAnalysisRequest(
        prompt=request.user_prompt,
        response_mode=ResponseMode.METRIC,
        activity_logs=activity_logs,
    )

    analysis_response = create_analysis(analysis_request)
    logger.info(f"Analysis created with RID: {analysis_response.analysis_rid}")

    return StartWorkflowResponse(
        analysis_rid=analysis_response.analysis_rid,
        output_config=analysis_response.output_config.model_dump(),
    )
