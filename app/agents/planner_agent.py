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

    # TODO: As of Dec. 2025, this is unused.  In the future, we want to
    # 1) Use LLM to determine plan and 2) use Amazon State Language.
    # See: https://states-language.net/spec.html#states-fields
    workflow = Workflow(
        start="Foo",
        graph=[
            Step(
                step_name="Foo",
                step_description="Foo",
                tool_name="Foo",
                next_step_name="END",
            ),
        ],
    )

    return workflow
