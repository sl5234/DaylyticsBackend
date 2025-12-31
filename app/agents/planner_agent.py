import logging
from app.models.plan import Workflow, Step

logger = logging.getLogger(__name__)


def handle_request(prompt: str) -> Workflow:
    """
    Plan agent that determines the appropriate data retrieval and analysis parameters.

    Args:
        prompt: Request prompt for activity analysis

    Returns:
        Workflow object containing the steps to execute
    """
    logger.info(f"Planner agent processing request: {prompt}")

    # TODO: As of Dec. 2025, we hardcode a default plan.  In the future, we want to
    # 1) Use LLM to determine plan and 2) use Amazon State Language.
    # See: https://states-language.net/spec.html#states-fields
    workflow = Workflow(
        start="GetTogglTrackActivityLogs",
        graph=[
            Step(
                step_name="GetTogglTrackActivityLogs",
                step_description="Get activity logs from Toggl Track API",
                tool_name="get_toggl_track_activity_logs",
                next_step_name="AnalyzeActivityLogs",
            ),
            Step(
                step_name="AnalyzeActivityLogs",
                step_description="Create analysis of activity logs",
                tool_name="create_analysis",
                next_step_name='END',
            ),
        ],
    )

    return workflow
