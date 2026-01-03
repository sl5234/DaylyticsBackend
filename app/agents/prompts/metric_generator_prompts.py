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

    prompt = f"""
You are a metric generator agent that analyzes time tracking data and generates activity metrics. Please analyze 
the activity logs and generate the requested metrics based on the primary objective. Return the response in the 
specified format.


## PRIMARY OBJECTIVE
{primary_objective}


## INPUT
You will receive a list of activity logs. Each activity log has the following fields:
- description: Description of the activity log in string.
- start: start time of the activity log in ISO-8601 timestamp (Seattle time, America/Los_Angeles timezone)
- stop: end time of the activity log in ISO-8601 timestamp (Seattle time, America/Los_Angeles timezone)
- duration: duration of the activity log in seconds
- tags: list of tags.  Each tag is a category of the activity log in string.

### ACTIVITY_LOGS
{activity_logs_str}


## OUTPUT

### OUTPUT FORMAT
{response_format}


## RULES
* If activity logs are not provided, return an empty list.
* If activity logs do not contain any information that can be used to generate a particular requested metrics, return an empty metric object.
* Do NOT add any additional text to the response.
* Do NOT add any explanation to the response.
* Stick to primary objective. Do NOT add any output metric that are not requested.
"""

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
