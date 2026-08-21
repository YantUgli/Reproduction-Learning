import pytest
from solution import paginate


def test_first_page_letters():
    assert paginate(list("abcdefg"), 1, 3) == ["a", "b", "c"]


def test_second_page_letters():
    assert paginate(list("abcdefg"), 2, 3) == ["d", "e", "f"]


def test_third_page_partial():
    assert paginate(list("abcdefg"), 3, 3) == ["g"]


def test_invalid_per_page_raises():
    with pytest.raises(ValueError):
        paginate(list("abc"), 1, 0)
