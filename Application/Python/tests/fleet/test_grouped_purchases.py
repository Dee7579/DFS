from dfs.domain.fleet.grouped_purchases import grouped_purchase_size, purchased_choice_count


def test_grouped_profiles_are_pairs():
    for profile_id in (6318, 6456, 6457, 6481, 6482, 6483):
        assert grouped_purchase_size(profile_id) == 2
    assert grouped_purchase_size(999999) == 1


def test_pair_consumes_one_priority_choice():
    assert purchased_choice_count(6481, 2) == 1
    assert purchased_choice_count(6481, 4) == 2
    assert purchased_choice_count(999999, 2) == 2


def test_incomplete_pair_is_not_undercharged():
    assert purchased_choice_count(6481, 1) == 1
    assert purchased_choice_count(6481, 3) == 2
