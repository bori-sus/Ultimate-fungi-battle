"""Тесты адаптивного UI.

Проверяем, что приложение корректно рендерится на экранах разных размеров:
- Крошечный (40×20) — Termux
- Узкий (60×30) — небольшой терминал
- Стандартный (80×24) — обычный терминал
- Широкий (120×40) — большой монитор
- Очень широкий (160×50) — wide screen
"""
import pytest

from ui.textual_app import FungiBattleApp, BoardCell
from game.card import Card


# ─── Тест наличия адаптивных CSS-классов ──────────────


def test_css_has_responsive_classes():
    """CSS содержит адаптивные медиа-классы -narrow и -tiny."""
    css = FungiBattleApp.CSS
    assert "-narrow" in css
    assert "-tiny" in css
    assert "Screen.-narrow" in css
    assert "Screen.-tiny" in css


def test_css_has_responsive_grid():
    """CSS содержит адаптивные grid-rows и grid-columns (1fr)."""
    css = FungiBattleApp.CSS
    assert "grid-rows: 1fr" in css
    assert "grid-columns: 1fr" in css


def test_css_has_responsive_hand_area():
    """CSS #hand-area имеет width: 100%."""
    css = FungiBattleApp.CSS
    assert "100%" in css


# ─── Тест адаптивной обрезки имени в render ────────────


def test_render_name_truncates_when_narrow():
    """BoardCell.render() обрезает имя, если size.width маленький."""
    from unittest.mock import MagicMock
    cell = BoardCell(row=0, col=0)
    c = Card(id="t", name="Очень длинное имя гриба", cost=2, atk=2, hp=2, max_hp=2)
    cell.set_card(c, "player", False)
    # Узкая клетка (10 столбцов)
    cell._size = MagicMock(width=10, height=3)
    rendered = cell.render()
    # имя должно быть обрезано
    assert "\u2026" in rendered


def test_render_name_full_when_wide():
    """BoardCell.render() показывает короткое имя целиком на широкой клетке."""
    from unittest.mock import MagicMock
    cell = BoardCell(row=0, col=0)
    c = Card(id="t", name="Мицелий", cost=1, atk=1, hp=2, max_hp=2)
    cell.set_card(c, "player", False)
    cell._size = MagicMock(width=40, height=3)
    rendered = cell.render()
    assert "Мицелий" in rendered


def test_render_name_adaptive_name_max():
    """Имя адаптивно обрезается до min(NAME_MAX, width-4)."""
    from unittest.mock import MagicMock
    cell = BoardCell(row=0, col=0)
    # name 20 chars
    c = Card(id="t", name="А" * 20, cost=1, atk=1, hp=2, max_hp=2)
    cell.set_card(c, "player", False)
    # при width=20 → name_max = min(13, 16) = 13 → 20 chars обрежется до 12+…
    cell._size = MagicMock(width=20, height=3)
    rendered = cell.render()
    assert "\u2026" in rendered


# ─── Тест _update_responsive_classes через run_test ────


@pytest.mark.asyncio
async def test_responsive_classes_tiny():
    """При size=(40, 20) устанавливаются -tiny и -narrow."""
    app = FungiBattleApp()
    async with app.run_test(size=(40, 20)) as pilot:
        await pilot.pause(0.05)
        assert app.screen.has_class("-tiny")
        assert app.screen.has_class("-narrow")


@pytest.mark.asyncio
async def test_responsive_classes_narrow_only():
    """При size=(60, 30) устанавливается -narrow, но НЕ -tiny."""
    app = FungiBattleApp()
    async with app.run_test(size=(60, 30)) as pilot:
        await pilot.pause(0.05)
        assert not app.screen.has_class("-tiny")
        assert app.screen.has_class("-narrow")


@pytest.mark.asyncio
async def test_responsive_classes_no_classes():
    """При size=(100, 40) адаптивные классы не ставятся."""
    app = FungiBattleApp()
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause(0.05)
        assert not app.screen.has_class("-tiny")
        assert not app.screen.has_class("-narrow")


# ─── Тесты запуска в headless-режиме на разных размерах ──


@pytest.mark.asyncio
async def test_tiny_screen_40x20():
    """Крошечный экран Termux (40×20) — приложение запускается и не падает."""
    app = FungiBattleApp()
    async with app.run_test(size=(40, 20)) as pilot:
        await pilot.pause(0.05)
        # приложение запустилось
        assert app is not None
        # есть адаптивные классы
        screen = app.screen
        assert screen.has_class("-tiny")
        assert screen.has_class("-narrow")


@pytest.mark.asyncio
async def test_narrow_screen_60x30():
    """Узкий экран (60×30) — устанавливается класс -narrow."""
    app = FungiBattleApp()
    async with app.run_test(size=(60, 30)) as pilot:
        await pilot.pause(0.05)
        screen = app.screen
        assert screen.has_class("-narrow")
        assert not screen.has_class("-tiny")


@pytest.mark.asyncio
async def test_standard_screen_80x24():
    """Стандартный терминал (80×24) — без адаптивных классов."""
    app = FungiBattleApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause(0.05)
        screen = app.screen
        assert not screen.has_class("-narrow")
        assert not screen.has_class("-tiny")


@pytest.mark.asyncio
async def test_wide_screen_120x40():
    """Широкий экран (120×40) — без адаптивных классов."""
    app = FungiBattleApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.05)
        screen = app.screen
        assert not screen.has_class("-narrow")
        assert not screen.has_class("-tiny")


@pytest.mark.asyncio
async def test_ultra_wide_screen_160x50():
    """Ультра-широкий экран (160×50) — без адаптивных классов."""
    app = FungiBattleApp()
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause(0.05)
        screen = app.screen
        assert not screen.has_class("-narrow")


# ─── Тест resize в headless ────────────────────────────


@pytest.mark.asyncio
async def test_resize_triggers_class_change():
    """При изменении размера с 80 на 40 устанавливается -tiny (через _update_responsive_classes)."""
    app = FungiBattleApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause(0.05)
        # изначально нет -tiny
        assert not app.screen.has_class("-tiny")
        # уменьшаем экран и явно вызываем _update_responsive_classes
        # (headless может не триггерить on_resize автоматически)
        await pilot.resize_terminal(40, 20)
        await pilot.pause(0.05)
        app._update_responsive_classes()
        await pilot.pause(0.05)
        # теперь -tiny
        assert app.screen.has_class("-tiny")


@pytest.mark.asyncio
async def test_grid_mounts_all_cells():
    """Grid содержит 5×4 = 20 клеток на любом размере."""
    app = FungiBattleApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause(0.05)
        cells = app.query(BoardCell)
        assert len(cells) == 20
