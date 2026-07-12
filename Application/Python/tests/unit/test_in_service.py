from dfs.domain.in_service import is_available_in_year, parse_in_service


def test_open_ended_start():
    period = parse_in_service("2246+")
    assert period.start == 2246 and period.end is None
    assert not period.includes(2245)
    assert period.includes(2246)


def test_bounded_range_with_unicode_dash():
    period = parse_in_service("2219–2242")
    assert period.includes(2219)
    assert period.includes(2242)
    assert not period.includes(2243)


def test_until_form_used_by_ancients_shadows_and_vorlons():
    period = parse_in_service("Until 2261")
    assert period.start is None and period.end == 2261
    assert period.includes(1000)
    assert period.includes(2261)
    assert not period.includes(2262)


def test_from_and_only_forms():
    assert is_available_in_year("From 2259", 2259)
    assert not is_available_in_year("From 2259", 2258)
    assert is_available_in_year("2261 only", 2261)
    assert not is_available_in_year("2261 only", 2260)


def test_all_and_unknown():
    assert is_available_in_year("All", 9999)
    assert not is_available_in_year("Unknown", 2258)
