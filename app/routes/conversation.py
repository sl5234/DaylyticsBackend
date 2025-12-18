import logging
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.planner_agent import handle_request
from app.services.workflow_orchestrator import execute_workflow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversation", tags=["conversation"])


class StartConversationRequest(BaseModel):
    """Request model for StartConversation endpoint."""

    Prompt: str
    StartDate: str
    EndDate: str


class StartConversationResponse(BaseModel):
    """Response model for StartConversation endpoint."""

    result: dict


@router.post("/", response_model=StartConversationResponse)
def start_conversation(request: StartConversationRequest) -> StartConversationResponse:
    """
    Start a conversation workflow.

    Accepts a user prompt and date range, calls the plan agent to determine
    the workflow strategy, then executes each step of the workflow.

    Args:
        request: StartConversationRequest containing prompt, start_date, and end_date

    Returns:
        StartConversationResponse containing the final workflow execution results
    """
    logger.info(f"Received StartConversation request: {request.Prompt}")

    # Step 1: Call plan agent to determine strategy
    workflow = handle_request(request.Prompt, request.StartDate, request.EndDate)
    logger.info(f"Plan agent returned workflow with {len(workflow.graph)} steps")

    # Step 2: Execute workflow steps
    result = execute_workflow(workflow, request.StartDate, request.EndDate)
    logger.info("Workflow execution completed")

    return StartConversationResponse(result=result)
