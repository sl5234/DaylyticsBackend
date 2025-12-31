import logging

from fastapi import APIRouter
from app.models.plan import CreatePlanRequest, CreatePlanResponse
from app.agents.planner_agent import handle_request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("/", response_model=CreatePlanResponse)
def create_plan(request: CreatePlanRequest) -> CreatePlanResponse:
    """
    Create a workflow plan for activity analysis.

    Takes request parameters and uses the planner agent to determine
    the appropriate workflow strategy for data retrieval and analysis.

    Args:
        request: CreatePlanRequest containing prompt

    Returns:
        CreatePlanResponse containing the Workflow plan
    """
    logger.info(f"Creating plan for user prompt: {request.prompt}")

    workflow = handle_request(request.prompt)
    logger.info(f"Plan agent returned workflow with {len(workflow.graph)} steps")

    return CreatePlanResponse(workflow=workflow)
