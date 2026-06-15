"""Тесты рендера UI-виджетов.

Тестируем BoardCell и HandCard — обрезание имён, превью стат, подсветку.
"""
from game.card import Card
from ui.textual_app import BoardCell, HandCard


# ─── helpers ────────────────────────────────────────────


def _make_card(name="Мицелий", cost=1, atk=1, hp=2, effect_id=None, max_hp=None):
    return Card(
        id="test_" + name.replace(" ", "_"),
        name=name,
        cost=cost,
        atk=atk,
        hp=hp,
        max_hp=max_hp if max_hp is not None else hp,
        effect_id=effect_id,
    )


# ─── BoardCell: обрезание имён ─────────────────────────


def test_boardcell_truncates_long_name():
    c = _make_card(name="А" * 50)
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    # NAME_MAX = 13, последний символ — многоточие
    assert len(cell.card_name) <= 13
    assert cell.card_name.endswith("\u2026")


def test_boardcell_short_name_not_truncated():
    c = _make_card(name="Мицелий")
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    assert cell.card_name == "Мицелий"


def test_boardcell_exact_max_length_not_truncated():
    """Имя ровно NAME_MAX символов — НЕ обрезается (без …)."""
    name = "А" * BoardCell.NAME_MAX
    c = _make_card(name=name)
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    assert cell.card_name == name
    assert "\u2026" not in cell.card_name


def test_boardcell_one_over_truncated():
    """Имя NAME_MAX+1 — обрезается до NAME_MAX-1 + …."""
    name = "А" * (BoardCell.NAME_MAX + 1)
    c = _make_card(name=name)
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    assert len(cell.card_name) == BoardCell.NAME_MAX
    assert cell.card_name.endswith("\u2026")


# ─── BoardCell: статы и эффект ────────────────────────


def test_boardcell_stats_field():
    c = _make_card(atk=3, hp=5, cost=4)
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    assert cell.card_stats == "3/5"
    assert cell.card_cost == "c:4"


def test_boardcell_effect_short_codes():
    """Для каждого известного эффекта есть короткий код."""
    cases = {
        "glow": "GLW", "heal1": "HL1", "heal2": "HL2",
        "gold": "G+1", "gold3": "G+3",
        "poison": "PSN", "deadly_poison": "DPS",
        "fortify": "FRT", "swift": "SWF",
        "drain": "DRN", "spiky": "SPK",
        "double_strike": "DBL", "taunt": "TNT",
        "stink": "STK", "growth": "GRW", "spores": "SPR",
    }
    for eff_id, expected_short in cases.items():
        c = _make_card(effect_id=eff_id)
        cell = BoardCell(row=0, col=0)
        cell.set_card(c, "player", False)
        assert cell.card_effect == expected_short, (
            f"effect {eff_id}: expected {expected_short}, got {cell.card_effect}"
        )


def test_boardcell_no_effect_empty():
    c = _make_card(effect_id=None)
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    assert cell.card_effect == ""


def test_boardcell_unknown_effect_empty():
    c = _make_card(effect_id="nonexistent")
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    assert cell.card_effect == ""


# ─── BoardCell: рендер ────────────────────────────────


def test_boardcell_render_contains_name():
    c = _make_card(name="Мицелий", atk=2, hp=3, cost=2)
    cell = BoardCell(row=3, col=0)
    cell.set_card(c, "player", True)
    rendered = cell.render()
    assert "Мицелий" in rendered
    assert "2/3" in rendered
    assert "c:2" in rendered
    assert "⚡" in rendered  # prepared


def test_boardcell_render_player_arrow():
    c = _make_card()
    cell = BoardCell(row=3, col=0)
    cell.set_card(c, "player", False)
    assert "▲" in cell.render()


def test_boardcell_render_enemy_arrow():
    c = _make_card()
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "enemy", False)
    assert "▼" in cell.render()


def test_boardcell_render_empty():
    cell = BoardCell(row=0, col=0)
    rendered = cell.render()
    assert "[" in rendered and "]" in rendered  # заглушка пустой клетки


def test_boardcell_render_with_cursor():
    c = _make_card()
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", False)
    cell.set_cursor(True)
    rendered = cell.render()
    assert "▸" in rendered and "◂" in rendered


def test_boardcell_render_with_target_highlight():
    c = _make_card()
    cell = BoardCell(row=3, col=0)
    cell.set_card(c, "player", False)
    cell.set_highlight(col=True, target=True)
    rendered = cell.render()
    assert "►" in rendered and "◄" in rendered


# ─── BoardCell: подсветка ──────────────────────────────


def test_boardcell_highlight_states():
    cell = BoardCell(row=0, col=0)
    assert cell.highlight_col is False
    assert cell.highlight_target is False
    assert cell.highlight_invalid is False

    cell.set_highlight(col=True)
    assert cell.highlight_col is True

    cell.set_highlight(target=True)
    assert cell.highlight_target is True

    cell.set_highlight(invalid=True)
    assert cell.highlight_invalid is True

    cell.clear_highlight()
    assert cell.highlight_col is False
    assert cell.highlight_target is False
    assert cell.highlight_invalid is False


# ─── HandCard: обрезание имён ─────────────────────────


def test_handcard_truncates_long_name():
    c = _make_card(name="Б" * 50)
    hc = HandCard(c, idx=0)
    # имя в label обрезано
    assert "…" in hc.label
    # или длина <= NAME_MAX+...


def test_handcard_short_name_kept():
    c = _make_card(name="Мицелий", atk=1, hp=2, cost=1)
    hc = HandCard(c, idx=0)
    assert "Мицелий" in hc.label
    assert "1/2" in hc.label
    assert "c:1" in hc.label


def test_handcard_index_in_label():
    c = _make_card()
    hc = HandCard(c, idx=2)
    assert "[3]" in hc.label  # idx+1


def test_handcard_selected_prefix():
    c = _make_card()
    hc = HandCard(c, idx=0, sel=True)
    assert "▸" in hc.label
    # выбран
    assert hc.selected is True


def test_handcard_unselected_no_prefix():
    c = _make_card()
    hc = HandCard(c, idx=0, sel=False)
    assert "▸" not in hc.label


def test_handcard_effect_in_label():
    c = _make_card(name="Ядовитый", cost=3, atk=2, hp=2, effect_id="poison")
    hc = HandCard(c, idx=0)
    assert "PSN" in hc.label


# ─── BoardCell: очистка при установке None ──────────────


def test_boardcell_clear_on_empty():
    c = _make_card()
    cell = BoardCell(row=0, col=0)
    cell.set_card(c, "player", True)
    assert cell.has_card is True
    # теперь очищаем
    cell.set_card(None, "", False)
    assert cell.has_card is False
    assert cell.card_name == ""
    assert cell.card_stats == ""
    assert cell.card_cost == ""
    assert cell.card_effect == ""
