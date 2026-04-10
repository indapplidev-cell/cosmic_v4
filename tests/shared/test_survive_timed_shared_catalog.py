from shared.constants.survive_timed_levels import (
    get_all_profiles,
    get_default_level_number,
    get_level_profile,
    get_max_level_number,
)


def test_survive_timed_shared_catalog_contract() -> None:
    profiles = get_all_profiles()

    assert get_default_level_number() == 1
    assert get_max_level_number() == 10
    assert len(profiles) == 10
    assert get_level_profile(1).level_code == "survive_timed_level_01"
    assert get_level_profile(10).level_code == "survive_timed_level_10"
    assert get_level_profile(0).level_number == 1
    assert get_level_profile(999).level_number == 10
    assert tuple(profile.level_number for profile in profiles) == tuple(range(1, 11))
    assert len({profile.level_code for profile in profiles}) == len(profiles)

