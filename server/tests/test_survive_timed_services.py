from types import SimpleNamespace

from server.services.modes.survive_timed.campaign_progress_service import _apply_level_success


def test_apply_level_success_does_not_regress_completed_campaign() -> None:
    row = SimpleNamespace(
        last_completed_level_number=10,
        current_level_number=10,
        campaign_completed=True,
        completed_at="2026-04-03T10:00:00Z",
    )

    _apply_level_success(row, 2)

    assert row.last_completed_level_number == 10
    assert row.current_level_number == 10
    assert row.campaign_completed is True
    assert row.completed_at == "2026-04-03T10:00:00Z"
