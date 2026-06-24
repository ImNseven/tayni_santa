import pytest

from apps.events.draw import assign_santas


@pytest.mark.parametrize("n", range(2, 51))
def test_invariants_hold_for_many_sizes(n):
    ids = list(range(n))
    pairs = assign_santas(ids)

    assert set(pairs.keys()) == set(ids)
    assert set(pairs.values()) == set(ids)
    assert all(santa != ward for santa, ward in pairs.items())


def test_forms_single_cycle():
    ids = list(range(10))
    pairs = assign_santas(ids)

    start = ids[0]
    seen = []
    current = start
    for _ in range(len(ids)):
        current = pairs[current]
        seen.append(current)
    assert set(seen) == set(ids)
    assert current == start


def test_requires_at_least_two():
    with pytest.raises(ValueError):
        assign_santas([1])
    with pytest.raises(ValueError):
        assign_santas([])


def test_works_with_uuid_like_keys():
    ids = ["a", "b", "c", "d"]
    pairs = assign_santas(ids)
    assert all(santa != ward for santa, ward in pairs.items())
    assert set(pairs.keys()) == set(ids)
