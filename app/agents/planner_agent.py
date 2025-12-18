import logging
from app.models.plan import Workflow, Step

logger = logging.getLogger(__name__)


def handle_request(prompt: str, start_date: str, end_date: str) -> Workflow:
    """
    Conversational agent that takes a user's prompt and determines the appropriate
    data retrieval and analysis parameters.

    Args:
        prompt: User's question or request about their activity
        start_date: Start date for activity log retrieval (YYYY-MM-DD format)
        end_date: End date for activity log retrieval (YYYY-MM-DD format)

    Returns:
        Workflow object containing the steps to execute
    """
    logger.info(
        f"Planner agent processing request: {prompt} for date range {start_date} to {end_date}"
    )

    # TODO: We want to use LLM.  As of Dec. 2025, we hardcode a default plan.
    # When we implement a more sophisticated planner, we can use Amazon State Language.
    # https://states-language.net/spec.html#states-fields
    workflow = Workflow(
        start="GetTogglTrackActivityLogs",
        graph=[
            Step(
                name="GetTogglTrackActivityLogs",
                description="Get activity logs from Toggl Track API",
                tool="get_toggl_track_activity_logs",
                next="AnalyzeActivityLogs",
            ),
            Step(
                name="AnalyzeActivityLogs",
                description="Create analysis of activity logs",
                tool="create_analysis",
                next=None,
            ),
        ],
    )

    return workflow
