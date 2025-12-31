import logging
from typing import Dict, Any, Optional
from app.models.plan import Workflow, Step
from app.services.toggl_service import get_toggl_track_activity_logs
from app.models.analysis import CreateAnalysisRequest, ResponseMode
from app.routes.analysis import create_analysis

logger = logging.getLogger(__name__)


def execute_workflow(
    workflow: Workflow, start_date: str, end_date: str
) -> Dict[str, Any]:
    """
    Execute a workflow by running each step in sequence.

    Steps are executed based on the 'next' field, starting from the 'start' step.
    Each step's tool is called with the appropriate parameters.

    Args:
        workflow: Workflow object containing the steps to execute
        start_date: Start date for the workflow execution
        end_date: End date for the workflow execution

    Returns:
        Dictionary containing the final results from workflow execution
    """
    logger.info(f"Executing workflow starting with step: {workflow.start}")

    # Create a map of step names to steps for easy lookup
    step_map = {step.step_name: step for step in workflow.graph}

    # Track results from each step
    step_results: Dict[str, Any] = {}
    current_step_name: str = workflow.start

    # Execute steps in sequence
    while current_step_name is not 'END':
        if current_step_name not in step_map:
            logger.error(f"Step '{current_step_name}' not found in workflow graph")
            break

        step = step_map[current_step_name]
        logger.info(f"Executing step: {step.step_name} - {step.step_description}")

        # Execute the step's tool
        result = _execute_step_tool(step, start_date, end_date, step_results)
        step_results[step.step_name] = result

        # Move to next step
        current_step_name = step.next_step_name
        logger.info(f"Step {step.step_name} completed, moving to: {current_step_name}")

    logger.info(f"Workflow execution completed. Executed {len(step_results)} steps")
    return step_results


def _execute_step_tool(
    step: Step, start_date: str, end_date: str, previous_results: Dict[str, Any]
) -> Any:
    """
    Execute a single step's tool.

    Args:
        step: Step object to execute
        start_date: Start date parameter
        end_date: End date parameter
        previous_results: Results from previous steps

    Returns:
        Result from executing the step's tool
    """
    tool = step.tool_name

    if tool == "get_toggl_track_activity_logs":
        logger.info("Calling toggl_service.get_toggl_track_activity_logs")
        return get_toggl_track_activity_logs(start_date, end_date)

    elif tool == "create_analysis":
        logger.info("Calling analysis.create_analysis")
        activity_logs = previous_results.get("GetTogglTrackActivityLogs")
        if activity_logs is None:
            raise ValueError(
                "Activity logs not found from previous step 'GetTogglTrackActivityLogs'"
            )
        analysis_request = CreateAnalysisRequest(
            StartDate=start_date,
            EndDate=end_date,
            ResponseMode=ResponseMode.METRIC,
            ActivityLogs=activity_logs,
        )
        analysis_response = create_analysis(analysis_request)
        return analysis_response.model_dump()

    else:
        logger.warning(f"Unknown tool: {tool}")
        return {"error": f"Unknown tool: {tool}"}
