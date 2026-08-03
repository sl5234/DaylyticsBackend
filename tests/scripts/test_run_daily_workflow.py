import importlib.util
import sys
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "run_daily_workflow.py"
)


@pytest.fixture(scope="module")
def run_daily_workflow():
    """Import the script as a module without requiring AWS credentials.

    The script does `from app.config import settings` at import time, which
    only constructs a pydantic Settings object (no AWS calls happen until
    functions are actually invoked), so a plain import is safe here.
    """
    spec = importlib.util.spec_from_file_location("run_daily_workflow", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_daily_workflow"] = module
    spec.loader.exec_module(module)
    return module


SEATTLE_TZ = ZoneInfo("America/Los_Angeles")


class TestGetDefaultTargetDate:
    def test_defaults_to_yesterday(self, run_daily_workflow):
        now = datetime(2026, 3, 10, 23, 59, 0, tzinfo=SEATTLE_TZ)
        target_date = run_daily_workflow._get_default_target_date(now)
        assert target_date.isoformat() == "2026-03-09"

    def test_crosses_month_boundary(self, run_daily_workflow):
        now = datetime(2026, 3, 1, 0, 5, 0, tzinfo=SEATTLE_TZ)
        target_date = run_daily_workflow._get_default_target_date(now)
        assert target_date.isoformat() == "2026-02-28"


class TestGetTargetDayRange:
    def test_matches_documented_example(self, run_daily_workflow):
        # (2026 DST starts 03/08, so 03/10 is already PDT, -07:00.)
        target_date = date(2026, 3, 10)
        start, end = run_daily_workflow._get_target_day_range(target_date, SEATTLE_TZ)
        assert start == "2026-03-10T00:00:00-07:00"
        assert end == "2026-03-10T23:59:59-07:00"

    def test_single_calendar_day_span(self, run_daily_workflow):
        target_date = date(2026, 7, 4)
        start, end = run_daily_workflow._get_target_day_range(target_date, SEATTLE_TZ)
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        assert start_dt.date() == end_dt.date() == target_date

    def test_handles_dst_offset(self, run_daily_workflow):
        # July is daylight saving time (PDT, -07:00) in America/Los_Angeles
        target_date = date(2026, 7, 4)
        start, end = run_daily_workflow._get_target_day_range(target_date, SEATTLE_TZ)
        assert start == "2026-07-04T00:00:00-07:00"
        assert end == "2026-07-04T23:59:59-07:00"


class TestFormatMinutes:
    def test_formats_whole_hours_and_minutes(self, run_daily_workflow):
        assert run_daily_workflow._format_minutes("438.15") == "7h 18m"

    def test_formats_over_24_hours(self, run_daily_workflow):
        # BedTimePerDay/UnrecordedTimePerDay etc. can exceed 1440 minutes.
        assert run_daily_workflow._format_minutes("1480.05") == "24h 40m"

    def test_zero(self, run_daily_workflow):
        assert run_daily_workflow._format_minutes("0.0") == "0h 0m"

    def test_empty_value(self, run_daily_workflow):
        assert run_daily_workflow._format_minutes("") == "N/A"

    def test_non_numeric_value_passed_through(self, run_daily_workflow):
        assert run_daily_workflow._format_minutes("n/a") == "n/a"


class TestFormatCsvAsTable:
    def test_renders_aligned_table(self, run_daily_workflow, tmp_path):
        csv_path = tmp_path / "AnalysisOutput2026-08-01.csv"
        csv_path.write_text(
            "Day,WakeUpTimePerDay,TotalWorkTimePerDay\n"
            "08/01/2026,438.15,0.0\n"
        )

        table = run_daily_workflow._format_csv_as_table(str(csv_path))

        assert "Date: 08/01/2026" in table
        assert "Metric" in table and "Value" in table
        assert "WakeUpTimePerDay" in table and "7h 18m" in table
        assert "TotalWorkTimePerDay" in table and "0h 0m" in table
        # No raw comma-separated line should remain.
        assert "438.15,0.0" not in table

    def test_multiple_date_rows_produce_separate_blocks(
        self, run_daily_workflow, tmp_path
    ):
        csv_path = tmp_path / "AnalysisOutput.csv"
        csv_path.write_text(
            "Day,TotalWorkTimePerDay\n08/01/2026,60\n08/02/2026,120\n"
        )

        table = run_daily_workflow._format_csv_as_table(str(csv_path))

        assert "Date: 08/01/2026" in table
        assert "Date: 08/02/2026" in table
        assert "1h 0m" in table
        assert "2h 0m" in table


class TestBuildSuccessDetail:
    def test_includes_formatted_table(self, run_daily_workflow, tmp_path):
        csv_path = tmp_path / "AnalysisOutput2026-08-01.csv"
        csv_path.write_text("Day,TotalWorkTimePerDay\n08/01/2026,120\n")

        detail = run_daily_workflow._build_success_detail(str(csv_path))

        assert str(csv_path) in detail
        assert "TotalWorkTimePerDay" in detail
        assert "2h 0m" in detail
        assert "08/01/2026,120" not in detail

    def test_falls_back_when_csv_unreadable(self, run_daily_workflow, tmp_path):
        missing_path = tmp_path / "does_not_exist.csv"

        detail = run_daily_workflow._build_success_detail(str(missing_path))

        assert str(missing_path) in detail
        assert "completed successfully" in detail

    def test_includes_s3_uri_when_provided(self, run_daily_workflow, tmp_path):
        csv_path = tmp_path / "AnalysisOutput2026-08-01.csv"
        csv_path.write_text("Day,TotalWorkTimePerDay\n08/01/2026,120\n")

        detail = run_daily_workflow._build_success_detail(
            str(csv_path), s3_uri="s3://my-bucket/AnalysisOutput2026-08-01.csv"
        )

        assert "Also uploaded to s3://my-bucket/AnalysisOutput2026-08-01.csv" in detail

    def test_omits_s3_note_when_not_provided(self, run_daily_workflow, tmp_path):
        csv_path = tmp_path / "AnalysisOutput2026-08-01.csv"
        csv_path.write_text("Day,TotalWorkTimePerDay\n08/01/2026,120\n")

        detail = run_daily_workflow._build_success_detail(str(csv_path))

        assert "Also uploaded" not in detail


class TestUploadCsvToS3:
    def test_uploads_with_filename_as_key_and_returns_uri(
        self, run_daily_workflow, tmp_path
    ):
        csv_path = tmp_path / "AnalysisOutput2026-08-01.csv"
        csv_path.write_text("Day,TotalWorkTimePerDay\n08/01/2026,120\n")

        mock_s3_client = MagicMock()
        mock_aws_clients = MagicMock()
        mock_aws_clients.get_s3_client.return_value = mock_s3_client

        s3_uri = run_daily_workflow._upload_csv_to_s3(
            str(csv_path), "my-bucket", mock_aws_clients
        )

        mock_s3_client.upload_file.assert_called_once_with(
            str(csv_path), "my-bucket", "AnalysisOutput2026-08-01.csv"
        )
        assert s3_uri == "s3://my-bucket/AnalysisOutput2026-08-01.csv"


class TestLambdaHandler:
    def test_defaults_to_yesterday_and_uploads_to_configured_bucket(
        self, run_daily_workflow, monkeypatch
    ):
        mock_run = MagicMock()
        monkeypatch.setattr(run_daily_workflow, "_run", mock_run)

        run_daily_workflow.lambda_handler({}, None)

        args, kwargs = mock_run.call_args
        called_target_date = args[0] if args else kwargs["target_date"]
        expected = run_daily_workflow._get_default_target_date(
            datetime.now(SEATTLE_TZ)
        )
        assert called_target_date == expected
        assert kwargs.get("output_dir", args[1] if len(args) > 1 else None) == "/tmp"
        assert kwargs.get("s3_bucket") == run_daily_workflow.settings.s3_output_bucket

    def test_honors_date_override_in_event(self, run_daily_workflow, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setattr(run_daily_workflow, "_run", mock_run)

        run_daily_workflow.lambda_handler({"date": "2026-08-01"}, None)

        args, kwargs = mock_run.call_args
        called_target_date = args[0] if args else kwargs["target_date"]
        assert called_target_date == date(2026, 8, 1)

    def test_handles_empty_event(self, run_daily_workflow, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setattr(run_daily_workflow, "_run", mock_run)

        run_daily_workflow.lambda_handler(None, None)

        mock_run.assert_called_once()


class TestMain:
    def test_exits_nonzero_on_failure(self, run_daily_workflow, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["run_daily_workflow.py"])
        monkeypatch.setattr(
            run_daily_workflow, "_run", MagicMock(side_effect=RuntimeError("boom"))
        )

        with pytest.raises(SystemExit) as exc_info:
            run_daily_workflow.main()
        assert exc_info.value.code == 1

    def test_uses_desktop_output_dir(self, run_daily_workflow, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["run_daily_workflow.py"])
        mock_run = MagicMock()
        monkeypatch.setattr(run_daily_workflow, "_run", mock_run)

        run_daily_workflow.main()

        _, kwargs = mock_run.call_args
        args = mock_run.call_args.args
        output_dir = kwargs.get("output_dir", args[1] if len(args) > 1 else None)
        assert output_dir == "~/Desktop/activityLogsDailyAnalysis"


class TestWorkflowRunEvent:
    def test_success_message_format(self, run_daily_workflow):
        event = run_daily_workflow.WorkflowRunEvent(
            status=run_daily_workflow.WorkflowRunStatus.SUCCESS,
            start_date="2026-03-10T00:00:00-08:00",
            end_date="2026-03-10T23:59:59-08:00",
            detail="Workflow completed successfully.",
        )
        assert event.subject == "Daylytics daily workflow success"
        assert "SUCCESS" in event.message
        assert "Workflow completed successfully." in event.message

    def test_failure_message_format(self, run_daily_workflow):
        event = run_daily_workflow.WorkflowRunEvent(
            status=run_daily_workflow.WorkflowRunStatus.FAILURE,
            start_date="2026-03-10T00:00:00-08:00",
            end_date="2026-03-10T23:59:59-08:00",
            detail="Error: boom",
        )
        assert event.subject == "Daylytics daily workflow failure"
        assert "FAILURE" in event.message
        assert "Error: boom" in event.message
