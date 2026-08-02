"""
Runs the Daylytics workflow for yesterday by default.

Intended to be invoked on a schedule (e.g. via launchd or cron), not run
interactively. Pulls activity logs from the Toggl Track API (TOGGL_API mode)
so no manual PDF download is required. Publishes an SNS notification on both
success and failure; exits non-zero on failure so the scheduler's own
failure logging picks it up too.

start_workflow() extends its raw Toggl fetch one full day past the
requested end_date, so a "yesterday" target's fetch window still reaches
into today and can include a currently-running (unstopped) time entry.
That's fine: deserialize_time_entries() skips entries it can't parse rather
than aborting the batch, and an entry still running today isn't part of
yesterday's report anyway.

Usage:
    venv/bin/python scripts/run_daily_workflow.py
    venv/bin/python scripts/run_daily_workflow.py --date 2026-08-01
"""

import argparse
import csv
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.dagger.aws_clients import AWSClients  # noqa: E402
from app.models.toggl import ActivityLogSource, InputConfig  # noqa: E402
from app.routes.workflow import StartWorkflowRequest, start_workflow  # noqa: E402

SEATTLE_TZ = ZoneInfo("America/Los_Angeles")

LOG_PATH = REPO_ROOT / "logs" / "daily_workflow.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WorkflowRunStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@dataclass
class WorkflowRunEvent:
    """Outcome of one scheduled run, used to build the SNS notification."""

    status: WorkflowRunStatus
    start_date: str
    end_date: str
    detail: str

    @property
    def subject(self) -> str:
        return f"Daylytics daily workflow {self.status.value.lower()}"

    @property
    def message(self) -> str:
        return (
            f"Status: {self.status.value}\n"
            f"Fetch window: {self.start_date} to {self.end_date}\n\n"
            f"{self.detail}"
        )


def _get_default_target_date(now: datetime) -> date:
    """
    Default target day: yesterday, relative to `now`'s date.

    Args:
        now: Timezone-aware "current time" (Seattle time)

    Returns:
        The target calendar date
    """
    return (now - timedelta(days=1)).date()


def _get_target_day_range(target_date: date, tzinfo) -> tuple[str, str]:
    """
    Compute the ISO-8601 start/end for a single target calendar day.

    Deliberately just the one calendar day (00:00:00 to 23:59:59) -
    start_workflow()/get_toggl_track_activity_logs() already pad the raw
    Toggl fetch by a full day on each side internally to catch
    overnight-crossing entries, so no extra padding is needed here.
    Widening this range would instead cause _get_dates_in_range() to report
    metrics for multiple calendar days per run.

    Args:
        target_date: The calendar date to build the range for
        tzinfo: Timezone to build the range in (Seattle time)

    Returns:
        Tuple of (start_date, end_date) as ISO-8601 strings
    """
    start = datetime(
        target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=tzinfo
    )
    end = start.replace(hour=23, minute=59, second=59)
    return start.isoformat(), end.isoformat()


def _format_minutes(value: str) -> str:
    """Format a minutes value (as stored in the CSV) as e.g. "7h 18m"."""
    if not value:
        return "N/A"
    try:
        total_minutes = float(value)
    except ValueError:
        return value
    hours, minutes = divmod(round(total_minutes), 60)
    return f"{hours}h {minutes}m"


def _format_csv_as_table(csv_path: str) -> str:
    """
    Render the output CSV as a human-readable table: one aligned
    Metric/Value block per date row, instead of raw comma-separated text.
    """
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    blocks = []
    for row in rows:
        day = row.get("Day", "unknown date")
        metrics = {column: value for column, value in row.items() if column != "Day"}
        label_width = max((len(label) for label in metrics), default=len("Metric"))

        lines = [
            f"Date: {day}",
            f"{'Metric':<{label_width}}  Value",
            f"{'-' * label_width}  -----",
        ]
        for label, value in metrics.items():
            lines.append(f"{label:<{label_width}}  {_format_minutes(value)}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def _build_success_detail(csv_path: str) -> str:
    """
    Build the success notification body, rendering the output CSV as a
    readable table so the numbers are visible directly in the email/SMS
    without needing to open the file.
    """
    try:
        table = _format_csv_as_table(csv_path)
    except OSError:
        logger.exception(f"Failed to read CSV at {csv_path} for notification")
        return f"Workflow completed successfully. CSV written to {csv_path}."
    return f"Workflow completed successfully. CSV written to {csv_path}.\n\n{table}"


def _notify(event: WorkflowRunEvent) -> None:
    """
    Publish a run-outcome notification to SNS. Never raises - a notification
    failure should not mask the original workflow result or crash the script.
    """
    try:
        aws_clients = AWSClients(region_name=None)
        aws_clients.initialize()
        sns_client = aws_clients.get_sns_client()
        sns_client.publish(
            TopicArn=settings.sns_topic_arn,
            Subject=event.subject,
            Message=event.message,
        )
        logger.info(f"Published {event.status.value} notification to SNS")
    except Exception:
        logger.exception("Failed to publish SNS notification")


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help=(
            "Target day to analyze, as YYYY-MM-DD. Defaults to 2 days "
            "before today if omitted."
        ),
    )
    return parser.parse_args(argv)


def main() -> None:
    args = _parse_args()
    now = datetime.now(SEATTLE_TZ)
    target_date = (
        datetime.strptime(args.date, "%Y-%m-%d").date()
        if args.date
        else _get_default_target_date(now)
    )
    start_date, end_date = _get_target_day_range(target_date, SEATTLE_TZ)

    logger.info(f"Running daily workflow for {start_date} to {end_date}")

    try:
        aws_clients = AWSClients(region_name=None)
        aws_clients.initialize()
        settings.set_aws_clients(aws_clients)

        request = StartWorkflowRequest(
            start_date=start_date,
            end_date=end_date,
            input_config=InputConfig(mode=ActivityLogSource.TOGGL_API),
            output_path="~/Desktop/activityLogsDailyAnalysis",
        )
        response = start_workflow(request)
        logger.info("Daily workflow completed successfully")
        _notify(
            WorkflowRunEvent(
                status=WorkflowRunStatus.SUCCESS,
                start_date=start_date,
                end_date=end_date,
                detail=_build_success_detail(response.output_path),
            )
        )
    except Exception as e:
        logger.exception("Daily workflow run failed")
        _notify(
            WorkflowRunEvent(
                status=WorkflowRunStatus.FAILURE,
                start_date=start_date,
                end_date=end_date,
                detail=f"Error: {e}\n\nSee {LOG_PATH} for full details.",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
