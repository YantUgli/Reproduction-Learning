from solution import add


def test_positif():
    assert add(2, 3) == 5


def test_nol():
    assert add(-1, 1) == 0


def test_negatif():
    assert add(-4, -6) == -10


def test_besar():
    assert add(1_000_000, 2_000_000) == 3_000_000
