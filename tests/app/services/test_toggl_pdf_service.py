from pathlib import Path

import pytest

from app.services.toggl_pdf_service import (
    _build_iso_datetime,
    _get_time_entries_from_pdf,
    _normalize_null_separators,
    _parse_duration_to_seconds,
    _parse_tags,
    _parse_time_date_column,
    get_toggl_track_activity_logs_from_pdf,
)

SAMPLE_PDF_PATH = (
    Path(__file__).resolve().parents[2]
    / "DO_NOT_COMMIT_LOCAL_FIXTURES"
    / "toggl_sample.pdf"
)

requires_sample_pdf = pytest.mark.skipif(
    not SAMPLE_PDF_PATH.exists(),
    reason=(
        "Sample Toggl PDF not found. Copy a Toggl Track PDF export to "
        f"{SAMPLE_PDF_PATH} to run these tests locally."
    ),
)


class TestNormalizeNullSeparators:
    """Some Toggl PDF exports embed a font that decodes ':' and '-' as '\\x00'."""

    def test_colon_inside_time(self):
        assert _normalize_null_separators("10\x0030") == "10:30"

    def test_colon_inside_duration(self):
        assert _normalize_null_separators("0\x0011\x0027") == "0:11:27"

    def test_dash_between_times(self):
        assert (
            _normalize_null_separators("10\x0030 \x00 10\x0041")
            == "10:30 - 10:41"
        )

    def test_leaves_normal_text_unchanged(self):
        assert _normalize_null_separators("10:30 - 10:41") == "10:30 - 10:41"

    def test_leaves_dash_placeholder_unchanged(self):
        assert _normalize_null_separators("-") == "-"


class TestParseTags:
    """The narrow TAGS column gets word-wrapped by pdfplumber, inserting '\\n'."""

    def test_single_tag_no_wrap(self):
        assert _parse_tags("shower") == ["shower"]

    def test_single_tag_wrapped_mid_word(self):
        assert _parse_tags("bed_tim\ne") == ["bed_time"]

    def test_single_tag_wrapped_multiple_times(self):
        assert _parse_tags("applicati\non_buildi\nng") == ["application_building"]

    def test_multiple_tags_wrapped_after_comma(self):
        assert _parse_tags("dog,\nwalk") == ["dog", "walk"]

    def test_multiple_tags_no_wrap(self):
        assert _parse_tags("dog, walk") == ["dog", "walk"]

    def test_empty_string(self):
        assert _parse_tags("") == []

    def test_whitespace_only(self):
        assert _parse_tags("   ") == []


class TestParseDurationToSeconds:
    def test_hours_minutes_seconds(self):
        assert _parse_duration_to_seconds("8:32:06") == 8 * 3600 + 32 * 60 + 6

    def test_minutes_seconds(self):
        assert _parse_duration_to_seconds("32:06") == 32 * 60 + 6

    def test_dash_placeholder(self):
        assert _parse_duration_to_seconds("-") == 0

    def test_empty_string(self):
        assert _parse_duration_to_seconds("") == 0


class TestParseTimeDateColumn:
    def test_same_day_entry(self):
        start_time, end_time, start_date, end_date = _parse_time_date_column(
            "19:58 - 20:14\n10/26/2025"
        )
        assert (start_time, end_time, start_date, end_date) == (
            "19:58",
            "20:14",
            "10/26/2025",
            None,
        )

    def test_entry_spanning_midnight(self):
        start_time, end_time, start_date, end_date = _parse_time_date_column(
            "21:42 - 06:15\n10/26/2025 - 10/27/2025"
        )
        assert (start_time, end_time, start_date, end_date) == (
            "21:42",
            "06:15",
            "10/26/2025",
            "10/27/2025",
        )

    def test_unparseable_time_raises(self):
        with pytest.raises(ValueError):
            _parse_time_date_column("not a time\n10/26/2025")


class TestBuildIsoDatetime:
    def test_builds_seattle_iso_datetime(self):
        result = _build_iso_datetime("10/26/2025", "21:42")
        assert result == "2025-10-26T21:42:00-07:00"

    def test_handles_dst_offset_change(self):
        # Late Feb is standard time (PST, -08:00) in America/Los_Angeles
        result = _build_iso_datetime("02/16/2026", "09:00")
        assert result == "2026-02-16T09:00:00-08:00"


@requires_sample_pdf
class TestSamplePdfExtraction:
    """Integration tests against a real Toggl Track PDF export.

    These reproduce a real-world bug: this PDF's embedded font decodes
    ':' and '-' as '\\x00', and the narrow TAGS column gets word-wrapped
    with embedded '\\n'. Both used to cause every row to be dropped or
    mis-tagged; these tests pin down the fixed behavior.
    """

    def test_extracts_entries_from_all_pages(self):
        raw_entries = _get_time_entries_from_pdf(SAMPLE_PDF_PATH)
        assert len(raw_entries) == 38

    def test_no_entry_has_null_bytes_in_duration_or_time_fields(self):
        raw_entries = _get_time_entries_from_pdf(SAMPLE_PDF_PATH)
        for entry in raw_entries:
            assert "\x00" not in entry["start"]
            assert "\x00" not in entry["stop"]

    def test_no_tag_has_embedded_newline(self):
        raw_entries = _get_time_entries_from_pdf(SAMPLE_PDF_PATH)
        for entry in raw_entries:
            for tag in entry["tags"]:
                assert "\n" not in tag

    def test_known_tags_are_parsed_correctly(self):
        raw_entries = _get_time_entries_from_pdf(SAMPLE_PDF_PATH)
        all_tags = {tag for entry in raw_entries for tag in entry["tags"]}
        assert "bed_time" in all_tags
        assert "application_building" in all_tags
        assert "groceries" in all_tags
        # These are the corrupted forms that would appear without the fix.
        assert "bed_tim\ne" not in all_tags
        assert "applicati\non_buildi\nng" not in all_tags

    def test_multi_tag_entry_splits_into_separate_tags(self):
        raw_entries = _get_time_entries_from_pdf(SAMPLE_PDF_PATH)
        dog_walk_entries = [
            entry
            for entry in raw_entries
            if "dog" in entry["tags"] and "walk" in entry["tags"]
        ]
        assert len(dog_walk_entries) > 0
        for entry in dog_walk_entries:
            assert entry["tags"] == ["dog", "walk"]

    def test_get_activity_logs_filters_by_date_range(self):
        entries = get_toggl_track_activity_logs_from_pdf(
            [str(SAMPLE_PDF_PATH)],
            "2026-02-15T00:00:00-08:00",
            "2026-02-17T23:59:59-08:00",
        )
        assert len(entries) == 26
        for entry in entries:
            assert entry.start.year == 2026
            assert entry.tags, "every entry in the fixture PDF has at least one tag"

    def test_get_activity_logs_from_multiple_pdf_paths(self):
        entries = get_toggl_track_activity_logs_from_pdf(
            [str(SAMPLE_PDF_PATH), str(SAMPLE_PDF_PATH)],
            "2026-02-15T00:00:00-08:00",
            "2026-02-17T23:59:59-08:00",
        )
        # Same file passed twice should double every matching entry.
        assert len(entries) == 52
