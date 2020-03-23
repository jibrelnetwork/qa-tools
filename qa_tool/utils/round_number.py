from decimal import Decimal
from math import ceil


def round_down(n, decimals=2):
    n = Decimal(str(n))
    multiplier = 10 ** decimals
    return float(int(n * multiplier) / multiplier)


def round_up(n, decimals=2):
    n = Decimal(str(n))
    multiplier = 10 ** decimals
    return float(ceil(n * multiplier) / multiplier)


class TestCMActions:

    def test_round_up_2(self):
        assert round_up(123.331) == 123.34

    def test_round_up_not_change(self):
        assert round_up(123.330) == 123.33

    def test_round_up_many(self):
        assert round_up(123.331111, 5) == 123.33112

    def test_round_down_2(self):
        assert round_down(123.339) == 123.33

    def test_round_down_not_change(self):
        assert round_down(123.330) == 123.33

    def test_round_down_many(self):
        assert round_down(123.3399999, 5) == 123.33999


if __name__ == '__main__':
    from qa_tool import run_test
    run_test(__file__)
