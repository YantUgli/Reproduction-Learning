import pytest
from solution import paginate


def test_first_page():
    assert paginate([1, 2, 3, 4, 5], 1, 2) == [1, 2]


def test_middle_page():
    assert paginate([1, 2, 3, 4, 5], 2, 2) == [3, 4]


def test_last_partial_page():
    assert paginate([1, 2, 3, 4, 5], 3, 2) == [5]


def test_out_of_range_is_empty():
    assert paginate([1, 2, 3], 5, 2) == []


def test_invalid_page_raises():
    with pytest.raises(ValueError):
        paginate([1, 2, 3], 0, 2)
