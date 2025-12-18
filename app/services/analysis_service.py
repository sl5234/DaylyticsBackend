from app.models.toggl import TogglTimeEntry
from app.models.activity import ActivityMetric, Period, Unit


def _generate_activity_metric(time_entry: TogglTimeEntry) -> ActivityMetric:
    """
    Generate an ActivityMetric from a TogglTimeEntry.

    Converts a TogglTimeEntry into an ActivityMetric with appropriate
    period, unit, value, and title based on the time entry data.

    Args:
        time_entry: TogglTimeEntry object to convert

    Returns:
        ActivityMetric object
    """
    # Extract date from start time
    entry_date = time_entry.start.date()

    # Convert duration from seconds to hours for the value
    duration_hours = time_entry.duration / 3600.0

    # Create ActivityMetric
    activity_metric = ActivityMetric(
        date=entry_date,
        period=Period.ONE_DAY,  # Default to 1day period
        unit=Unit.HRS,  # Use hours as the unit
        value=duration_hours,
        title=time_entry.description,
    )

    return activity_metric
