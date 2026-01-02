from typing import List
from app.models.toggl import TogglTimeEntry


def build_metric_generator_prompt(
    primary_objective: str,
    activity_logs: List[TogglTimeEntry],
    response_format: str,
) -> str:
    """
    Build system prompt for metric generator agent.

    Args:
        primary_objective: User's primary objective/prompt describing what metrics they want
        activity_logs: List of TogglTimeEntry objects to analyze
        response_format: Format specification for the response (e.g., JSON schema)

    Returns:
        Complete prompt string for the LLM
    """
    activity_logs_str = _format_activity_logs(activity_logs)

    prompt = f"""You are a metric generator agent that analyzes time tracking data and generates activity metrics.

PRIMARY_OBJECTIVE:
{primary_objective}

ACTIVITY_LOGS:
{activity_logs_str}

RESPONSE_FORMAT:
{response_format}

RULES:
* If activity logs are not provided, return an empty list.

Please analyze the activity logs and generate the requested metrics based on the primary objective. Return the response in the specified format."""

    return prompt


def _format_activity_logs(activity_logs: List[TogglTimeEntry]) -> str:
    """
    Format activity logs into a readable string format.

    Args:
        activity_logs: List of TogglTimeEntry objects

    Returns:
        Formatted string representation of activity logs
    """
    formatted_entries = []
    for i, entry in enumerate(activity_logs, 1):
        entry_str = f"""Entry {i}:
  - Tags: {', '.join(entry.tags) if entry.tags else 'None'}
  - Description: {entry.description}
  - Start: {entry.start.isoformat()}
  - Stop: {entry.stop.isoformat()}
  - Duration: {entry.duration} seconds ({entry.duration / 60:.2f} minutes)"""
        formatted_entries.append(entry_str)

    return "\n\n".join(formatted_entries)
