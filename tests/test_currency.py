"""Coin arithmetic (models.currency)."""

import pytest

from models.currency import parse_coins, format_coins


class TestParseCoins:
    @pytest.mark.parametrize("s,expected", [
        ("5 gp", 500),
        ("2 sp", 20),
        ("7 cp", 7),
        ("1 pp", 1000),
        ("3 ep", 150),
        ("1 gp 4 sp", 140),
        ("1 gp 4 sp 2 cp", 142),
        ("1.5 gp", 150),
        ("5 gold", 500),
        ("2 silver pieces", 20),
        ("5gp", 500),          # no space
        ("  5 gp  ", 500),     # surrounding whitespace
    ])
    def test_parses_amounts(self, s, expected):
        assert parse_coins(s) == expected

    @pytest.mark.parametrize("s", [
        "", None, "Varies", "by arrangement", "2-5 gp", "2–5 gp",
        "negotiable", "priceless", "free", "5", "nonsense",
    ])
    def test_unparseable_is_none(self, s):
        assert parse_coins(s) is None


class TestFormatCoins:
    @pytest.mark.parametrize("cp,expected", [
        (0, "0 cp"),
        (7, "7 cp"),
        (20, "2 sp"),
        (140, "1 gp 4 sp"),
        (142, "1 gp 4 sp 2 cp"),
        (500, "5 gp"),
        (1000, "10 gp"),
        (None, ""),
    ])
    def test_formats(self, cp, expected):
        assert format_coins(cp) == expected

    def test_round_trips(self):
        for cp in (0, 7, 20, 140, 142, 500, 1000, 12345):
            assert parse_coins(format_coins(cp)) == cp
