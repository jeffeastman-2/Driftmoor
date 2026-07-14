"""Character coin purse (models.character purse_cp + helpers, loader parsing)."""

from models.character import Character


def _char(cp=0):
    return Character(id="x", name="X", race="Human", character_type="npc", purse_cp=cp)


class TestPurseHelpers:
    def test_default_is_empty(self):
        assert _char().purse_cp == 0

    def test_can_afford(self):
        c = _char(150)
        assert c.can_afford(150) is True
        assert c.can_afford(151) is False
        assert c.can_afford(0) is True

    def test_debit_spends_when_affordable(self):
        c = _char(150)
        assert c.debit(40) is True
        assert c.purse_cp == 110

    def test_debit_refuses_when_broke_and_is_noop(self):
        c = _char(30)
        assert c.debit(40) is False
        assert c.purse_cp == 30

    def test_debit_rejects_negative(self):
        c = _char(30)
        assert c.debit(-10) is False
        assert c.purse_cp == 30

    def test_credit_adds(self):
        c = _char(30)
        c.credit(70)
        assert c.purse_cp == 100

    def test_credit_ignores_negative(self):
        c = _char(30)
        c.credit(-5)
        assert c.purse_cp == 30

    def test_transfer_conserves_total(self):
        a, b = _char(100), _char(20)
        assert a.debit(30)
        b.credit(30)
        assert (a.purse_cp, b.purse_cp) == (70, 50)


class TestPurseLoading:
    def test_parses_wealth_section(self):
        from models.character_loader import _parse_purse
        text = "# IDENTITY.md — Someone\n\n## Wealth\n- **Purse:** 15 gp\n"
        assert _parse_purse(text) == 1500

    def test_absent_purse_defaults_to_zero(self):
        from models.character_loader import _parse_purse
        assert _parse_purse("# IDENTITY.md — Someone\n\nNo wealth line here.") == 0

    def test_unparseable_purse_defaults_to_zero(self):
        from models.character_loader import _parse_purse
        assert _parse_purse("- **Purse:** a few coins") == 0

    def test_real_characters_load_with_a_purse_field(self):
        # No character authors a Purse yet, so all default to 0 — but the field
        # is present and integer on every loaded character.
        from pathlib import Path
        from models.character_loader import load_all_characters
        chars = load_all_characters(Path("scenario/people"))
        assert chars, "expected characters to load"
        assert all(isinstance(c.purse_cp, int) for c in chars)
