from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_survive_timed_source_of_truth_layout() -> None:
    assert not (PROJECT_ROOT / "client/gameplay/modes/survive_timed/contracts.py").exists()
    assert not (PROJECT_ROOT / "client/gameplay/modes/survive_timed/registry.py").exists()
    assert not (PROJECT_ROOT / "client/gameplay/modes/survive_timed/profiles").exists()
    assert (PROJECT_ROOT / "shared/contracts/survive_timed.py").exists()
    assert (PROJECT_ROOT / "shared/constants/survive_timed_levels.py").exists()
