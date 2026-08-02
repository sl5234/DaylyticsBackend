import logging

from app.services.helpers.toggl_service_helper import deserialize_time_entries


def _valid_entry(entry_id: int, **overrides) -> dict:
    entry = {
        "id": entry_id,
        "tags": ["work"],
        "description": "model eval",
        "start": "2026-08-01T10:00:00-07:00",
        "stop": "2026-08-01T11:00:00-07:00",
        "duration": 3600,
    }
    entry.update(overrides)
    return entry


class TestDeserializeTimeEntries:
    def test_deserializes_valid_entries(self):
        entries = [_valid_entry(1), _valid_entry(2)]
        result = deserialize_time_entries(entries)
        assert len(result) == 2

    def test_skips_currently_running_entry_without_aborting_batch(self, caplog):
        # A Toggl entry that's still actively running has stop=None.
        entries = [
            _valid_entry(1),
            _valid_entry(2, stop=None),
            _valid_entry(3),
        ]
        with caplog.at_level(logging.WARNING):
            result = deserialize_time_entries(entries)

        assert len(result) == 2
        assert {e.description for e in result} == {"model eval"}
        assert any("Skipping time entry 2" in message for message in caplog.messages)

    def test_all_entries_running_returns_empty_list(self):
        entries = [_valid_entry(1, stop=None), _valid_entry(2, stop=None)]
        result = deserialize_time_entries(entries)
        assert result == []

    def test_skips_entry_missing_other_required_fields_too(self, caplog):
        entries = [_valid_entry(1), _valid_entry(2, description=None)]
        with caplog.at_level(logging.WARNING):
            result = deserialize_time_entries(entries)
        assert len(result) == 1
        assert any("Skipping time entry 2" in message for message in caplog.messages)
