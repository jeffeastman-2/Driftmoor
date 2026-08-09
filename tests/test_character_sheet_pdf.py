import pytest

pytest.importorskip("reportlab")

from character_generation import CharacterDraft
from character_sheet_pdf import character_sheet_pdf, modifier, proficiency_bonus


def test_modifier_and_proficiency_progression():
    assert modifier(8) == -1
    assert modifier(10) == 0
    assert modifier(17) == 3
    assert proficiency_bonus(1) == 2
    assert proficiency_bonus(5) == 3


def test_character_sheet_is_two_page_pdf():
    pypdf = pytest.importorskip("pypdf")
    draft = CharacterDraft(
        name="Mara Vell", values_and_drives=["Protect lost pilgrims"],
        voice_and_manner=["Speaks softly under pressure"],
    )
    data = character_sheet_pdf(draft)
    assert data.startswith(b"%PDF")
    assert len(pypdf.PdfReader(__import__("io").BytesIO(data)).pages) == 2
