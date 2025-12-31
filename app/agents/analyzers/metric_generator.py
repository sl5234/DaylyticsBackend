from typing import List, Dict
from collections import defaultdict
from datetime import date, datetime, time
from app.models.toggl import TogglTimeEntry
from app.models.activity import ActivityMetric, Period, Unit


def _generate_wake_up_time_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate wake up time metric from time entries.

    Finds the entry with the latest start time and creates an ActivityMetric
    with that time as minutes since midnight (00:00).

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with the wake up time in minutes
    """
    if not time_entries:
        raise ValueError("Cannot generate wake up time metric from empty time entries")

    # Find the entry with the latest start time
    latest_entry = max(time_entries, key=lambda entry: entry.start)

    wake_up_minutes = latest_entry.start.hour * 60 + latest_entry.start.minute

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=float(wake_up_minutes),
        title="Wake Up Time",
    )


def _generate_bed_time_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate bed time metric from time entries.

    Finds the entry with the latest stop time and creates an ActivityMetric
    with that time as minutes since midnight (00:00).

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with the bed time in minutes
    """
    if not time_entries:
        raise ValueError("Cannot generate bed time metric from empty time entries")

    # Find the entry with the latest stop time
    latest_entry = max(time_entries, key=lambda entry: entry.stop)

    bed_time_minutes = latest_entry.stop.hour * 60 + latest_entry.stop.minute

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=float(bed_time_minutes),
        title="Bed Time",
    )


def _generate_workout_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate workout metric from time entries.

    Sums up the durations of all workout time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total workout time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Workout Time",
    )


def _generate_family_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate family metric from time entries.

    Sums up the durations of all family time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total family time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Family Time",
    )


def _generate_research_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate research metric from time entries.

    Sums up the durations of all research time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total research time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Research Time",
    )


def _generate_reading_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate reading metric from time entries.

    Sums up the durations of all reading time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total reading time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Reading Time",
    )


def _generate_amazon_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate Amazon metric from time entries.

    Sums up the durations of all Amazon time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total Amazon time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Amazon Time",
    )


def _generate_app_dev_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate app development metric from time entries.

    Sums up the durations of all app development time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total app development time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="App Building Time",
    )


def _generate_finance_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate finance metric from time entries.

    Sums up the durations of all finance time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total finance time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Finance Time",
    )


def _generate_language_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate language learning metric from time entries.

    Sums up the durations of all language learning time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total language study time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Language Study Time",
    )


def _generate_unrecorded_time_metric(
    time_entries: List[TogglTimeEntry],
) -> ActivityMetric:
    """
    Generate unrecorded time metric from time entries.

    Calculates the total time without any time entry for a given day (00:00 to 23:59).
    Only considers the portion of time entries that fall within the current day,
    handling entries that span across day boundaries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with unrecorded time in minutes
    """
    today = date.today()

    if time_entries and time_entries[0].start.tzinfo is not None:
        entry_tz = time_entries[0].start.tzinfo
        day_start = datetime.combine(today, time.min, tzinfo=entry_tz)
        day_end = datetime.combine(today, time(23, 59, 59), tzinfo=entry_tz)
    else:
        day_start = datetime.combine(today, time.min)
        day_end = datetime.combine(today, time(23, 59, 59))

    total_recorded_seconds = 0.0
    for entry in time_entries:
        entry_start = max(entry.start, day_start)
        entry_stop = min(entry.stop, day_end)
        if entry_start < entry_stop:
            recorded_seconds = (entry_stop - entry_start).total_seconds()
            total_recorded_seconds += recorded_seconds

    total_minutes_in_day = 24 * 60
    total_recorded_minutes = total_recorded_seconds / 60.0
    unrecorded_minutes = total_minutes_in_day - total_recorded_minutes

    return ActivityMetric(
        date=today,
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=unrecorded_minutes,
        title="Unrecorded Time",
    )


def _generate_total_work_time_metric(
    time_entries: List[TogglTimeEntry],
) -> ActivityMetric:
    """
    Generate total work time metric from time entries.

    Sums up the durations of all work time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total work time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Total Work Time",
    )


def _generate_dating_metric(time_entries: List[TogglTimeEntry]) -> ActivityMetric:
    """
    Generate dating metric from time entries.

    Sums up the durations of all dating time entries.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        ActivityMetric object with total dating time in minutes
    """
    total_duration_seconds = sum(entry.duration for entry in time_entries)
    total_duration_minutes = total_duration_seconds / 60.0

    return ActivityMetric(
        date=date.today(),
        period=Period.ONE_DAY,
        unit=Unit.MINS,
        value=total_duration_minutes,
        title="Dating Time",
    )


def _categorize_time_entry(time_entry: TogglTimeEntry) -> List[str]:
    """
    Categorize a time entry into one or more categories based on tags.

    Args:
        time_entry: TogglTimeEntry object to categorize

    Returns:
        List of category names that this entry belongs to
    """
    tags_lower = [tag.lower() for tag in time_entry.tags]

    if "sleep" in tags_lower:
        return ["WakeUpTime", "BedTime"]

    if "cardio" in tags_lower or "workout" in tags_lower:
        return ["WorkoutTime"]

    if any(
        tag in tags_lower
        for tag in ["brother", "parent", "mom", "mom_call", "parent_call", "dad_call"]
    ):
        return ["FamilyTime"]

    if "research" in tags_lower:
        return ["ResearchTime", "TotalWorkTime"]

    if "daily_reading" in tags_lower:
        return ["ReadingTime", "TotalWorkTime"]

    if "work" in tags_lower:
        return ["AmazonTime", "TotalWorkTime"]

    if "app" in tags_lower:
        return ["AppBuildingTime", "TotalWorkTime"]

    if any(
        tag in tags_lower
        for tag in ["daily_accounting", "weekly_accounting", "finance"]
    ):
        return ["FinanceTime"]

    if "language" in tags_lower:
        return ["LanguageStudyTime"]

    if "zexin" in tags_lower:
        return ["DatingTime"]

    return []


def generate_all_metrics(time_entries: List[TogglTimeEntry]) -> List[ActivityMetric]:
    """
    Generate all activity metrics from time entries.

    Iterates through time entries, categorizes each one, and calls the appropriate
    metric generator functions with categorized entries.

    TODO: This whole thing should be a LLM call.  As of Dec. 2025, this is
    deterministic rule based.

    Args:
        time_entries: List of TogglTimeEntry objects

    Returns:
        List of ActivityMetric objects from all metric generators
    """
    categorized_entries: Dict[str, List[TogglTimeEntry]] = defaultdict(list)

    for entry in time_entries:
        categories = _categorize_time_entry(entry)
        for category in categories:
            categorized_entries[category].append(entry)
    print(categorized_entries)

    all_metrics: List[ActivityMetric] = []

    if categorized_entries["WakeUpTime"]:
        all_metrics.append(
            _generate_wake_up_time_metric(categorized_entries["WakeUpTime"])
        )

    if categorized_entries["BedTime"]:
        all_metrics.append(_generate_bed_time_metric(categorized_entries["BedTime"]))

    if categorized_entries["WorkoutTime"]:
        all_metrics.append(_generate_workout_metric(categorized_entries["WorkoutTime"]))

    if categorized_entries["FamilyTime"]:
        all_metrics.append(_generate_family_metric(categorized_entries["FamilyTime"]))

    if categorized_entries["ResearchTime"]:
        all_metrics.append(
            _generate_research_metric(categorized_entries["ResearchTime"])
        )

    if categorized_entries["ReadingTime"]:
        all_metrics.append(_generate_reading_metric(categorized_entries["ReadingTime"]))

    if categorized_entries["AmazonTime"]:
        all_metrics.append(_generate_amazon_metric(categorized_entries["AmazonTime"]))

    if categorized_entries["AppBuildingTime"]:
        all_metrics.append(
            _generate_app_dev_metric(categorized_entries["AppBuildingTime"])
        )

    if categorized_entries["FinanceTime"]:
        all_metrics.append(_generate_finance_metric(categorized_entries["FinanceTime"]))

    if categorized_entries["LanguageStudyTime"]:
        all_metrics.append(
            _generate_language_metric(categorized_entries["LanguageStudyTime"])
        )

    if categorized_entries["DatingTime"]:
        all_metrics.append(_generate_dating_metric(categorized_entries["DatingTime"]))

    # Unrecorded time metrics (uses all entries)
    unrecorded_metric = _generate_unrecorded_time_metric(time_entries)
    all_metrics.append(unrecorded_metric)

    # Total work time metrics (uses all entries)
    total_work_metric = _generate_total_work_time_metric(time_entries)
    all_metrics.append(total_work_metric)

    print(all_metrics)
    return all_metrics
