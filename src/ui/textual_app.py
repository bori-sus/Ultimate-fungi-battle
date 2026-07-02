"""
Textual TUI для Ultimate Fungi Battle.

Управление:
  1-4       — выбрать карту в руке (или перевыбрать)
  a b c d e — выбрать колонну 1-5 (после выбора карты)
  s         — продать выбранную карту
  p         — пропустить ход
  q         — выход (с сохранением)
  стрелки   — курсор по полю
  Enter     — показать инфо о карте под курсором
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from typing import Optional
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Button
from textual.containers import Horizontal, Vertical, Container, Grid
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.screen import Screen
from textual import events
from game.engine import GameEngine
from game.card import Card
from game.save import save_game
from game.levels import list_levels, total_levels


# ─── helpers ────────────────────────────────────────────


def card_compact(card: Card) -> str:
    return f"{card.name}({card.atk}/{card.hp})"


def card_full(card: Card) -> str:
    txt = f"{card.name}\n"
    txt += f"  ATK: {card.atk}  HP: {card.hp}/{card.max_hp}\n"
    txt += f"  Cost: {card.cost}"
    if card.effect_id:
        txt += f"  [{card.effect_id}]"
    txt += f"\n  {card.description}"
    return txt


# ─── custom widgets ─────────────────────────────────────


class BoardCell(Widget):
    """Одна клетка поля 5×4 — перерисовывается через reactive."""

    DEFAULT_CSS = """
    BoardCell {
        width: 1fr;
        height: 1fr;
        background: #0f3460;
        border: solid #533483;
        text-align: center;
        padding: 0;
        margin: 0;
    }
    """

    # ширина имени в клетке (в символах) — верхняя граница
    NAME_MAX = 13
    # префиксы эффектов (одна буква + код)
    EFFECT_SHORT = {
        "glow": "GLW",
        "heal1": "HL1",
        "heal2": "HL2",
        "gold": "G+1",
        "gold3": "G+3",
        "poison": "PSN",
        "deadly_poison": "DPS",
        "fortify": "FRT",
        "swift": "SWF",
        "drain": "DRN",
        "spiky": "SPK",
        "double_strike": "DBL",
        "taunt": "TNT",
        "stink": "STK",
        "growth": "GRW",
        "spores": "SPR",
    }

    card_name: reactive[str] = reactive("")
    card_stats: reactive[str] = reactive("")
    card_cost: reactive[str] = reactive("")
    card_effect: reactive[str] = reactive("")
    side: reactive[str] = reactive("")
    prepared: reactive[bool] = reactive(False)
    has_cursor: reactive[bool] = reactive(False)
    has_card: reactive[bool] = reactive(False)
    # подсветка колонн
    highlight_col: reactive[bool] = reactive(False)   # колонна выбрана — вся колонна подсвечена
    highlight_target: reactive[bool] = reactive(False) # целевая ячейка (куда встанет)
    highlight_invalid: reactive[bool] = reactive(False) # запрещённая ячейка (нет золота/занята)

    def __init__(self, row: int, col: int, **kw):
        super().__init__(**kw)
        self.row = row
        self.col = col
        self._card_obj: Optional[Card] = None
        self._full_name: str = ""

    @staticmethod
    def _trunc(text: str, max_len: int) -> str:
        """Обрезать строку до max_len символов + …, если не влезает."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"

    def watch_has_card(self, val: bool):
        self.refresh()

    def watch_card_name(self, val: str):
        self.refresh()

    def watch_card_stats(self, val: str):
        self.refresh()

    def watch_card_cost(self, val: str):
        self.refresh()

    def watch_card_effect(self, val: str):
        self.refresh()

    def watch_side(self, val: str):
        self.refresh()

    def watch_prepared(self, val: bool):
        self.refresh()

    def watch_has_cursor(self, val: bool):
        self.refresh()

    def watch_highlight_col(self, val: bool):
        self._update_style()
        self.refresh()

    def watch_highlight_target(self, val: bool):
        self._update_style()
        self.refresh()

    def watch_highlight_invalid(self, val: bool):
        self._update_style()
        self.refresh()

    def _update_style(self):
        """Обновить цвета фона и рамки в зависимости от подсветки."""
        if self.highlight_target:
            self.styles.background = "#1a4a2e"
            self.styles.border = ("heavy", "#4ecca3")
        elif self.highlight_invalid:
            self.styles.background = "#3a0f0f"
            self.styles.border = ("dashed", "#e94560")
        elif self.highlight_col:
            self.styles.background = "#3d3520"
            self.styles.border = ("solid", "#f0c040")
        else:
            self.styles.background = "#0f3460"
            self.styles.border = ("solid", "#533483")

    def set_card(self, card: Optional[Card], owner: str, prep: bool):
        self._card_obj = card
        if card:
            self._full_name = card.name
            # card_name может быть обрезано в render() адаптивно
            self.card_name = card.name
            self.card_stats = f"{card.atk}/{card.hp}"
            self.card_cost = f"c:{card.cost}"
            self.card_effect = self.EFFECT_SHORT.get(card.effect_id or "", "")
            self.side = owner
            self.prepared = prep
            self.has_card = True
        else:
            self._full_name = ""
            self.card_name = ""
            self.card_stats = ""
            self.card_cost = ""
            self.card_effect = ""
            self.side = ""
            self.prepared = False
            self.has_card = False

    def set_cursor(self, val: bool):
        self.has_cursor = val

    def set_highlight(self, col: bool = False, target: bool = False, invalid: bool = False):
        self.highlight_col = col
        self.highlight_target = target
        self.highlight_invalid = invalid

    def clear_highlight(self):
        self.highlight_col = False
        self.highlight_target = False
        self.highlight_invalid = False

    def render(self):
        # адаптивная ширина имени: от размера клетки
        w = self.size.width if self.size else 13
        name_max = max(6, min(self.NAME_MAX, w - 4))  # минимум 6, максимум NAME_MAX
        if self.has_card:
            p_mark = "⚡" if self.prepared else " "
            side_arrow = "▼" if self.side == "enemy" else "▲"
            eff = self.card_effect
            cost = self.card_cost
            # обрезаем имя под текущую ширину
            full_name = self._full_name  # полное имя
            if len(full_name) > name_max:
                display_name = full_name[: name_max - 1] + "…"
            else:
                display_name = full_name
            line3 = (eff + " " + cost) if eff else ("     " + cost)
            name_display = display_name.center(name_max)
            text = (
                f"{side_arrow}{name_display}{p_mark}\n"
                f"  ATK:{self.card_stats:<6}\n"
                f"{line3}"
            )
        else:
            empty = "[" + " " * (name_max + 2) + "]"
            text = f"{empty}\n\n"
        if self.has_cursor:
            text = f"▸{text}◂"
        if self.highlight_target:
            text = f"►{text}◄"
        return text

    def on_mount(self):
        # Адаптивные размеры по ширине И высоте экрана (соотношение игральной карты)
        w = self.app.size.width if self.app and hasattr(self.app, "size") else 80
        h = self.app.size.height if self.app and hasattr(self.app, "size") else 24
        cw, ch = self._card_size_for(w, h)
        self.styles.width = cw
        self.styles.height = ch
        self.styles.min_width = cw
        self.styles.min_height = ch
        self.styles.background = "#0f3460"
        # Border убираем полностью — экономит место (2 строки)
        self.styles.border = ("none", "transparent")
        self.styles.text_align = "center"
        self.styles.padding = (0, 0)
        self.styles.margin = (0, 0, 0, 0)

    @staticmethod
    def _card_size_for(width: int, height: int = 0) -> tuple[int, int]:
        """Единый расчёт размера клетки/карты: cell_width x cell_height.

        ВЫСОТА > ШИРИНЫ в ~1.40 раз (как у игральной карты):
            Poker: 2.5" × 3.5"  → h/w = 1.40
            Magic: 63 × 88 мм   → h/w = 1.40

        Размеры (высота БОЛЬШЕ ширины):
            40×20:  3×4  h/w=1.33 — Termux портрет
            40×30:  4×5  h/w=1.25
            60×30:  4×5  h/w=1.25
            80×24:  3×4  h/w=1.33 — узкий стандарт
            100×40: 5×7  h/w=1.40 ✅ стандарт игральной карты!
            120×40: 5×7  h/w=1.40 ✅ стандарт!
        """
        # Адаптация по высоте и ширине экрана
        if height < 22:
            return 3, 4   # 40×20: мини
        elif height < 26:
            return 3, 4   # 80×24: узкий
        elif height < 32:
            return 4, 5   # 60×30, 40×30: средний
        elif height < 42:
            return 5, 7   # 100×40, 120×40: ✅ СТАНДАРТ КАРТЫ
        else:
            return 6, 8   # большой

    def on_click(self, event) -> None:
        """Тап/клик по клетке — выбрать её как целевую или поставить карту.

        В верхних рядах — перемещаем туда курсор (для просмотра).
        В нижнем ряду — ставим выбранную карту (если выбрана).
        """
        app = self.app
        if app is None:
            return
        # перемещаем курсор на эту клетку
        app.cursor_row = self.row
        app.cursor_col = self.col
        # обновить подсветку
        if self.row == app.engine.state.board.height - 1:
            # нижний ряд — это ряд игрока
            if app.phase == "pick_column" and app.selected_hand_idx is not None:
                # тап = поставить
                app._play_card(self.col)
            else:
                # перемещаем курсор
                app._refresh_column_highlight()
        else:
            # верхние ряды — перемещаем курсор
            app._refresh_column_highlight()


class HandCard(Widget):
    """Карта в руке — полноразмерная (4-5 строк: имя, ATK/HP, эффект, описание)."""

    label: reactive[str] = reactive("")
    selected: reactive[bool] = reactive(False)

    EFFECT_SHORT = BoardCell.EFFECT_SHORT
    NAME_MAX = 14
    # полное описание показывается только если хватает места
    DESCRIPTION_MIN_WIDTH = 18  # минимальная ширина для показа описания
    DESCRIPTION_MIN_HEIGHT = 4  # минимальная высота для показа описания

    def __init__(self, card: Card, idx: int, sel: bool = False, **kw):
        super().__init__(**kw)
        self._card = card
        self.idx = idx
        # reactive `selected` присваиваем явно, чтобы watch_selected сработал
        self.selected = sel
        # пересобираем label в зависимости от sel
        self._build_label(sel)
        if sel:
            self.set_class(True, "selected")

    def _build_label(self, sel: bool):
        """Собрать полное превью карты с центрированием.

        Полноразмерный формат (центрируется в карте):
        ▸ [1] Имя
            2/3  c:2  PSN
            Ядовитая атака +1
        """
        sel_prefix = "▸ " if sel else "  "
        c = self._card
        eff = self.EFFECT_SHORT.get(c.effect_id or "", "")
        w = self.size.width if self.size else 22
        h = self.size.height if self.size else 4
        # длина имени (адаптивно)
        name_max = max(6, min(self.NAME_MAX, w - 6))  # 6 = "[1] " + отступ
        name = c.name
        if len(name) > name_max:
            name = name[: name_max - 1] + "…"
        eff_part = f" {eff}" if eff else ""
        # первая строка: [N] Имя
        line1 = f"{sel_prefix}[{self.idx+1}] {name}"
        # вторая строка: ATK/HP  c:cost  EFFECT
        line2 = f"    {c.atk}/{c.hp}  c:{c.cost}{eff_part}"
        lines = [line1, line2]
        # описание показываем если хватает места
        if h >= 4 and c.description:
            desc_max = max(8, w - 4)
            desc = c.description
            if len(desc) > desc_max:
                desc = desc[: desc_max - 1] + "…"
            lines.append(f"    {desc}")
        # Центрируем: добавляем пустые строки сверху/снизу
        if h > len(lines):
            total_pad = h - len(lines)
            top_pad = total_pad // 2
            bot_pad = total_pad - top_pad
            lines = [""] * top_pad + lines + [""] * bot_pad
        self.label = "\n".join(lines)

    def watch_selected(self, val: bool):
        self._build_label(val)
        self.set_class(val, "selected")

    def watch_selected(self, val: bool):
        self._build_label(val)
        self.set_class(val, "selected")

    def render(self):
        return self.label

    def on_mount(self):
        # Адаптивные размеры (те же что у BoardCell — карта = размер клетки)
        w = self.app.size.width if self.app and hasattr(self.app, "size") else 80
        h = self.app.size.height if self.app and hasattr(self.app, "size") else 24
        from ui.textual_app import BoardCell
        cw, ch = BoardCell._card_size_for(w, h)
        self.styles.width = cw
        self.styles.height = ch
        self.styles.min_width = cw
        self.styles.min_height = ch
        self.styles.background = "#0f3460"
        # Border убираем — экономим место
        self.styles.border = ("none", "transparent")
        self.styles.padding = (0, 0)
        self.styles.margin = (0, 0, 0, 0)
        # Пересобираем label после первого layout (когда size станет известен)
        self.call_after_refresh(lambda: self._build_label(self.selected))

    def on_size(self) -> None:
        """При изменении размера пересобираем label адаптивно."""
        self._build_label(self.selected)

    def on_click(self, event) -> None:
        """Тап/клик по карте в руке — выбрать её для размещения."""
        app = self.app
        if app is None:
            return
        app._select_hand_card(self.idx)


class InfoPanel(Widget):
    """Панель информации о карте под курсором."""

    info_text: reactive[str] = reactive("")

    def show(self, card: Optional[Card]):
        if card:
            self.info_text = card_full(card)
        else:
            self.info_text = ""

    def render(self):
        return self.info_text

    def on_mount(self):
        self.styles.width = 30
        self.styles.height = 8
        self.styles.background = "#16213e"
        self.styles.border = ("solid", "#533483")
        self.styles.padding = 1
        self.styles.margin = (0, 0, 0, 1)


# ─── Game Over Screen ───────────────────────────────────


class GameOverScreen(Screen):
    """Экран окончания игры с опциями."""

    CSS = """
    GameOverScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.85);
    }
    #game-over-box {
        width: 50;
        height: auto;
        background: #1a1a2e;
        border: double #e94560;
        padding: 2 3;
        text-align: center;
    }
    #game-over-title {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
    }
    #game-over-stats {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin: 1 0;
        background: #16213e;
        border: solid #533483;
    }
    #game-over-stats Label {
        margin: 0 0 0 0;
    }
    #game-over-options {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    GameOverScreen Label.option-key {
        color: #f0c040;
        text-style: bold;
    }
    GameOverScreen Label.option-desc {
        color: #e0e0e0;
    }
    .victory-title {
        color: #4ecca3;
    }
    .defeat-title {
        color: #e94560;
    }
    """

    def __init__(self, winner: str, level_name: str, stats: dict, level_index: int, **kw):
        super().__init__(**kw)
        self.winner = winner
        self.level_name = level_name
        self.stats = stats
        self.level_index = level_index
        self.result = None  # будет установлено при выборе

    def compose(self) -> ComposeResult:
        is_victory = self.winner == "player"
        title_class = "victory-title" if is_victory else "defeat-title"
        title_text = "🎉  ПОБЕДА!" if is_victory else "💀  ПОРАЖЕНИЕ..."

        with Vertical(id="game-over-box"):
            # Title
            yield Label(f"{title_text}", id="game-over-title", classes=title_class)

            # Level info
            yield Label(f"Уровень: {self.level_name}")

            # Stats
            with Vertical(id="game-over-stats"):
                yield Label(f"Ходов сыграно:  {self.stats.get('turns_survived', 0)}")
                yield Label(f"Карт сыграно:   {self.stats.get('cards_played', 0)}")
                yield Label(f"Урона нанесено: {self.stats.get('damage_dealt', 0)}")
                yield Label(f"Золота получено: {self.stats.get('gold_earned', 0)}")

            # Options
            with Vertical(id="game-over-options"):
                yield Label("")

                # Restart option
                with Horizontal():
                    yield Label("[R]", classes="option-key")
                    yield Label("  Рестарт — начать уровень заново", classes="option-desc")

                # Next level (only if won)
                if is_victory:
                    nxt_lvl = self.level_index + 1
                    total_lvls = total_levels()
                    if nxt_lvl < total_lvls:
                        with Horizontal():
                            yield Label("[N]", classes="option-key")
                            yield Label(f"  Следующий уровень →", classes="option-desc")
                    else:
                        with Horizontal():
                            yield Label("[N]", classes="option-key")
                            yield Label(f"  ★ Финальный пройден! ★", classes="option-desc")

                # Quit
                with Horizontal():
                    yield Label("[Q]", classes="option-key")
                    yield Label("  Выход", classes="option-desc")

    def on_key(self, event: events.Key) -> None:
        if event.key == "r":
            self.result = "restart"
            self.dismiss()
        elif event.key == "n" and self.winner == "player":
            self.result = "next"
            self.dismiss()
        elif event.key == "q":
            self.result = "quit"
            self.dismiss()


# ─── main app ───────────────────────────────────────────


class FungiBattleApp(App):
    """Textual TUI для карточной игры."""

    CSS = """
    Screen {
        background: #1a1a2e;
        color: #e0e0e0;
    }
    Header { display: none; }
    Footer { display: none; }
    /* Контейнер всего приложения растягивается на весь экран */
    #app-root {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    /* Верхняя строка статусов: адаптивно */
    #top-bar {
        height: 1;
        width: 100%;
        background: #16213e;
        padding: 0 1;
    }
    #top-bar Label {
        width: auto;
        margin: 0 2 0 0;
    }
    #turn-label { color: #a0d6ff; }
    #hp-label { color: #e94560; }
    #gold-label { color: #f0c040; }
    #enemy-hp-label { color: #ff6b6b; }
    #level-label { color: #4ecca3; }
    /* Поле + инфо-панель: делим ширину */
    #main-area {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
    }
    /* Поле 5×4: адаптивные размеры (фиксированные по ширине экрана) */
    #board-grid {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
        grid-size: 5 4;
        grid-gutter: 0;
    }
    #info-panel {
        width: 1fr;
        min-width: 20;
        height: auto;
    }
    /* Рука: карточки растягиваются по ширине */
    #hand-area {
        width: 100%;
        height: auto;
        background: #16213e;
        layout: vertical;
        padding: 0;
        margin: 0;
        border: none;
    }
    #hand-area > Label {
        width: auto;
        margin: 0;
        height: 1;
        display: none;  /* скрыт — top-bar уже показывает HP/gold/turn */
    }
    #hand-cards {
        width: 100%;
        height: auto;
        padding: 0;
        margin: 0;
    }
    HandCard.selected {
        background: #533483;
        border: solid #e94560;
    }
    /* Статус-бар */
    #status-bar {
        height: 1;
        width: 100%;
        background: #16213e;
        padding: 0 1;
        color: #e0e0e0;
        display: none;  /* скрыт по умолчанию — top-bar показывает HP/gold */
    }
    /* Touch-панель с кнопками */
    #touch-panel {
        width: 100%;
        height: auto;
        background: #16213e;
        padding: 0;
        margin: 0;
        layout: vertical;
    }
    #touch-panel Horizontal {
        height: 1;
    }
    #touch-panel-row1, #touch-panel-row2, #touch-panel-row3 {
        width: 100%;
        height: auto;
        align: center middle;
    }
    .touch-btn {
        width: 1fr;
        min-width: 3;
        height: 1;
        margin: 0;
        background: #0f3460;
        border: none;
        color: #e0e0e0;
        text-style: bold;
        content-align: center middle;
    }
    .touch-btn:hover {
        background: #533483;
        border: solid #f0c040;
    }
    .touch-btn.active {
        background: #f0c040;
        color: #0f3460;
        border: solid #4ecca3;
    }
    .touch-btn.danger {
        background: #3a0f0f;
        border: solid #e94560;
        color: #e94560;
    }
    .touch-btn.primary {
        background: #1a4a2e;
        border: solid #4ecca3;
        color: #4ecca3;
    }
    .touch-spacer {
        width: 1;
    }
    /* Адаптация для маленьких экранов: < 80 столбцов */
    Screen.-narrow .info-card-extra { display: none; }
    Screen.-narrow #info-panel { display: none; }
    Screen.-narrow #board-grid { width: 100%; }
    Screen.-narrow #hand-area {
        padding: 0;
        margin: 0;
        border: none;
    }
    Screen.-narrow #touch-panel {
        height: auto;
    }
    Screen.-narrow .touch-btn { height: 1; }
    /* Стандартный режим (>=80) — touch-панель компактнее */
    /* Адаптация для очень маленьких экранов: < 50 столбцов (Termux портрет) */
    Screen.-tiny {
        layout: vertical;
    }
    Screen.-tiny #top-bar {
        height: 0;
        padding: 0;
        display: none;  /* освобождаем строку под клетки/руку */
    }
    Screen.-tiny #top-bar Label { margin: 0 0 0 1; }
    Screen.-tiny #main-area {
        height: auto;
        padding: 0;
    }
    Screen.-tiny #board-grid {
        width: 100%;
        height: auto;
    }
    Screen.-tiny #status-bar { display: none; }
    Screen.-tiny #hand-area {
        height: auto;
        padding: 0;
        margin: 0;
        border: none;
        background: #1a1a2e;
    }
    Screen.-tiny #hand-area > Label { display: none; }
    Screen.-tiny #hand-cards { height: 3; }
    Screen.-tiny HandCard { height: 3; }
    Screen.-tiny #touch-panel { display: none; }
    """

    BINDINGS = [
        Binding("1", "card_0", "1"),
        Binding("2", "card_1", "2"),
        Binding("3", "card_2", "3"),
        Binding("4", "card_3", "4"),
        Binding("a", "col_0", "a"),
        Binding("b", "col_1", "b"),
        Binding("c", "col_2", "c"),
        Binding("d", "col_3", "d"),
        Binding("e", "col_4", "e"),
        Binding("space", "play_at_cursor", "␣"),
        Binding("s", "sell", "Sell"),
        Binding("p", "pass", "Pass"),
        Binding("q", "quit", "Quit"),
        Binding("up", "cursor_up", "↑", priority=True),
        Binding("down", "cursor_down", "↓", priority=True),
        Binding("left", "cursor_left", "←", priority=True),
        Binding("right", "cursor_right", "→", priority=True),
        Binding("enter", "show_info", "Info", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.current_level = 0
        self.engine = self._create_engine()
        self.selected_hand_idx: Optional[int] = None
        self.phase: str = "main"  # 'main' | 'pick_column' | 'game_over'
        self.cursor_row = 0
        self.cursor_col = 0

    def _create_engine(self) -> GameEngine:
        """Создать движок для текущего уровня."""
        return GameEngine.create_for_level(self.current_level, seed=42)

    def _start_player_turn(self):
        """Начать ход игрока: золото + добор."""
        self.engine.begin_turn("player")

    # ─── compose ────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="top-bar"):
            yield Label("", id="level-label")
            yield Label("", id="turn-label")
            yield Label("", id="hp-label")
            yield Label("", id="gold-label")
            yield Label("", id="enemy-hp-label")
        with Horizontal(id="main-area"):
            yield Grid(id="board-grid")
            yield InfoPanel(id="info-panel")
        with Vertical(id="touch-panel"):
            with Horizontal(id="touch-panel-row1"):
                for i in range(1, 5):
                    yield Button(f"[{i}]", id=f"t-card-{i}", classes="touch-btn")
                for letter in "abcde":
                    yield Button(letter.upper(), id=f"t-col-{letter}", classes="touch-btn")
                yield Button("␣\nПоставить", id="t-play", classes="touch-btn primary")
                yield Button("$ Продать", id="t-sell", classes="touch-btn")
            with Horizontal(id="touch-panel-row2"):
                yield Button("←", id="t-left", classes="touch-btn")
                yield Button("↑", id="t-up", classes="touch-btn")
                yield Button("↓", id="t-down", classes="touch-btn")
                yield Button("→", id="t-right", classes="touch-btn")
                yield Button("✓ Пропуск", id="t-pass", classes="touch-btn")
        with Vertical(id="hand-area"):
            yield Label("Рука:")
            with Horizontal(id="hand-cards"):
                pass  # HandCard монтируются в _refresh_hand
        yield Static("Добро пожаловать! 1-4 выбрать карту, a-e колонна, s продать, p пропуск", id="status-bar")
        yield Footer()

    # ─── mount & refresh ────────────────────────────────

    def on_mount(self):
        # populate board grid
        grid = self.query_one("#board-grid", Grid)
        for r in range(4):
            for c in range(5):
                grid.mount(BoardCell(r, c))
        self._start_player_turn()
        self._refresh_all()
        # инициализировать адаптивные классы экрана
        self._update_responsive_classes()

    def on_resize(self, event) -> None:
        """При изменении размера экрана — обновить адаптивные классы и перерисовать."""
        self._update_responsive_classes()
        # перерисовать клетки, чтобы имена адаптировались под новую ширину
        for w in self.query(BoardCell):
            w.refresh()
        for w in self.query(HandCard):
            w._build_label(w.selected)
            w.refresh()

    def _update_responsive_classes(self) -> None:
        """Установить CSS-классы экрана по текущему размеру.

        - width < 50: -tiny и -narrow
        - 50 <= width < 80: -narrow
        - width >= 80: без адаптивных классов
        """
        try:
            size = self.size
        except Exception:
            return
        w = size.width
        screen = self.screen
        is_tiny = w < 50
        is_narrow = w < 80
        screen.set_class(is_tiny, "-tiny")
        screen.set_class(is_narrow, "-narrow")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Тап/клик по кнопке в touch-панели — эмуляция нажатия клавиши."""
        bid = event.button.id or ""
        # 1) карты 1-4
        if bid.startswith("t-card-"):
            try:
                idx = int(bid.split("-")[-1]) - 1
            except ValueError:
                return
            self._select_hand_card(idx)
            self._refresh_touch_panel()
        # 2) колонки a-e
        elif bid.startswith("t-col-"):
            letter = bid.split("-")[-1]
            col_map = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4}
            if letter in col_map:
                self._play_card(col_map[letter])
                self._refresh_touch_panel()
        # 3) остальные действия
        elif bid == "t-play":
            self.action_play_at_cursor()
            self._refresh_touch_panel()
        elif bid == "t-sell":
            self.action_sell()
            self._refresh_touch_panel()
        elif bid == "t-pass":
            self.action_pass()
            self._refresh_touch_panel()
        elif bid == "t-up":
            self.action_cursor_up()
        elif bid == "t-down":
            self.action_cursor_down()
        elif bid == "t-left":
            self.action_cursor_left()
        elif bid == "t-right":
            self.action_cursor_right()

    def _refresh_touch_panel(self) -> None:
        """Подсветить активные кнопки в touch-панели."""
        # карты — подсвечиваем выбранную
        for i in range(1, 5):
            btn = self.query_one(f"#t-card-{i}", Button)
            btn.set_class(self.selected_hand_idx == i - 1, "active")
        # колонки — красные/зелёные по доступности
        for letter, col in [("a", 0), ("b", 1), ("c", 2), ("d", 3), ("e", 4)]:
            btn = self.query_one(f"#t-col-{letter}", Button)
            if self.phase != "pick_column" or self.selected_hand_idx is None:
                btn.set_class(False, "active")
                btn.set_class(False, "danger")
                continue
            hand = self.engine.state.player.hand
            if self.selected_hand_idx >= len(hand):
                btn.set_class(False, "active")
                btn.set_class(False, "danger")
                continue
            card = hand[self.selected_hand_idx]
            target_row = self.engine.state.board.height - 1
            cell_data = self.engine.state.board.cell(target_row, col)
            occupied = cell_data.card is not None
            affordable = self.engine.state.player.gold >= card.cost
            if not affordable or occupied:
                btn.set_class(False, "active")
                btn.set_class(True, "danger")
            else:
                btn.set_class(True, "active")
                btn.set_class(False, "danger")

    def _refresh_all(self):
        self._refresh_top_bar()
        self._refresh_board()
        self._refresh_hand()
        self._refresh_info()
        self._refresh_cursor()
        self._refresh_column_highlight()
        self._refresh_touch_panel()
        self._refresh_column_highlight()

    def _refresh_top_bar(self):
        s = self.engine.state
        lvl_name = self.engine.state.level_config.get("name", f"Ур. {self.current_level + 1}")
        self.query_one("#level-label", Label).update(f"🏔 {lvl_name}")
        self.query_one("#turn-label", Label).update(f"Ход {self.engine.turn_number}")
        self.query_one("#hp-label", Label).update(f"❤ {s.player.hp}")
        self.query_one("#gold-label", Label).update(f"💰 {s.player.gold}")
        self.query_one("#enemy-hp-label", Label).update(f"Враг ❤ {s.enemy.hp}")

    def _refresh_board(self):
        board = self.engine.state.board
        cells = list(self.query(BoardCell))
        for cw in cells:
            r, c = cw.row, cw.col
            cell_data = board.cell(r, c)
            cw.set_card(cell_data.card, cell_data.owner or "", cell_data.prepared)

    def _refresh_hand(self):
        # карты монтируются в Horizontal #hand-cards, чтобы занимали всю ширину
        ha = self.query_one("#hand-area", Vertical)
        container = self.query_one("#hand-cards", Horizontal)
        # удаляем старые HandCard
        for w in list(container.children):
            if isinstance(w, HandCard):
                w.remove()
        # удаляем заглушку, если она есть
        try:
            placeholder = self.query_one("#hand-placeholder", Static)
            if placeholder and placeholder in container.children:
                placeholder.remove()
        except Exception:
            pass  # placeholder уже удалён
        hand = self.engine.state.player.hand
        for i, card in enumerate(hand):
            sel = (self.selected_hand_idx == i)
            hc = HandCard(card, i, sel=sel)
            if sel:
                hc.set_class(True, "selected")
            container.mount(hc)

    def _refresh_info(self):
        board = self.engine.state.board
        cell = board.cell(self.cursor_row, self.cursor_col)
        self.query_one("#info-panel", InfoPanel).show(cell.card)

    def _refresh_cursor(self):
        cells = list(self.query(BoardCell))
        for w in cells:
            w.set_cursor(w.row == self.cursor_row and w.col == self.cursor_col)

    def _clear_column_highlight(self):
        """Сбросить подсветку всех колонок."""
        for w in self.query(BoardCell):
            w.clear_highlight()

    def _refresh_column_highlight(self):
        """Подсветить колонки/целевую клетку, если выбрана карта для размещения."""
        # сначала сбросить
        self._clear_column_highlight()
        if self.phase != "pick_column" or self.selected_hand_idx is None:
            return
        hand = self.engine.state.player.hand
        if self.selected_hand_idx >= len(hand):
            return
        card = hand[self.selected_hand_idx]
        target_row = self.engine.state.board.height - 1  # row 3
        player = self.engine.state.player
        affordable = player.gold >= card.cost
        # 1) все клетки в нижнем ряду подсвечиваем по доступности
        for w in self.query(BoardCell):
            if w.row != target_row:
                continue
            cell_data = self.engine.state.board.cell(target_row, w.col)
            occupied = cell_data.card is not None
            if not affordable or occupied:
                w.set_highlight(col=True, invalid=True)
            else:
                w.set_highlight(col=True)
        # 2) превью: подсветить клетку под курсором ярче
        if self.cursor_row == target_row and affordable:
            for w in self.query(BoardCell):
                if w.row == target_row and w.col == self.cursor_col:
                    cell_data = self.engine.state.board.cell(target_row, self.cursor_col)
                    if cell_data.card is None:
                        w.set_highlight(col=True, target=True)

    def _set_status(self, msg: str):
        sb = self.query_one("#status-bar", Static)
        sb.update(msg)
        self.status_text = msg

    # ─── card selection (1-4) ───────────────────────────

    def action_card_0(self): self._select_hand_card(0)
    def action_card_1(self): self._select_hand_card(1)
    def action_card_2(self): self._select_hand_card(2)
    def action_card_3(self): self._select_hand_card(3)

    def _select_hand_card(self, idx: int):
        if self.phase == "game_over":
            return
        hand = self.engine.state.player.hand
        if idx >= len(hand):
            self._set_status(f"Нет карты {idx+1}")
            return
        # если та же карта уже выбрана и курсор в нижнем ряду — поставить
        if (self.phase == "pick_column"
                and self.selected_hand_idx == idx
                and self.cursor_row == self.engine.state.board.height - 1):
            self._play_card(self.cursor_col)
            return
        self.selected_hand_idx = idx
        self.phase = "pick_column"
        card = hand[idx]
        # подсказка про стоимость
        if self.engine.state.player.gold < card.cost:
            cost_hint = f" ⚠ нужно {card.cost} золота!"
        else:
            cost_hint = ""
        self._set_status(
            f"Карта: {card.name} (atk:{card.atk} hp:{card.hp} cost:{card.cost})"
            f"{cost_hint} — a-e или [␣] под курсором, 1-4 повтор, s продать"
        )
        self._refresh_hand()
        self._refresh_column_highlight()

    # ─── column selection (a-e) ─────────────────────────

    def action_col_0(self): self._play_card(0)
    def action_col_1(self): self._play_card(1)
    def action_col_2(self): self._play_card(2)
    def action_col_3(self): self._play_card(3)
    def action_col_4(self): self._play_card(4)

    def _play_card(self, col: int):
        if self.phase != "pick_column" or self.selected_hand_idx is None:
            self._set_status("Сначала выберите карту (1-4)")
            return
        hand = self.engine.state.player.hand
        if self.selected_hand_idx >= len(hand):
            self.selected_hand_idx = None
            self.phase = "main"
            self._set_status("Карта уже не в руке")
            self._refresh_hand()
            self._refresh_column_highlight()
            return
        card_id = hand[self.selected_hand_idx].id
        card_name = hand[self.selected_hand_idx].name
        ok = self.engine.play_card_by_id("player", card_id, col)
        if ok:
            self._set_status(f"✓ {card_name} → колонка {col+1}")
        else:
            self._set_status("✗ Недостаточно золота или ячейка занята")
        self.selected_hand_idx = None
        self.phase = "main"
        self._refresh_all()

    def action_play_at_cursor(self):
        """Поставить выбранную карту в колонку под курсором (пробел)."""
        if self.phase == "game_over":
            return
        if self.phase != "pick_column" or self.selected_hand_idx is None:
            self._set_status("Сначала выберите карту (1-4)")
            return
        target_row = self.engine.state.board.height - 1
        if self.cursor_row != target_row:
            self._set_status("Курсор должен быть в нижнем ряду")
            return
        self._play_card(self.cursor_col)

    # ─── sell ───────────────────────────────────────────

    def action_sell(self):
        if self.phase == "game_over":
            return
        if self.selected_hand_idx is None:
            self._set_status("Сначала выберите карту (1-4) для продажи")
            return
        ok = self.engine.sell_from_hand("player", self.selected_hand_idx)
        if ok:
            self._set_status("Карта продана")
        else:
            self._set_status("Не удалось продать")
        self.selected_hand_idx = None
        self.phase = "main"
        self._refresh_all()

    # ─── pass turn ─────────────────────────────────────

    def action_pass(self):
        if self.phase == "game_over":
            return
        self.selected_hand_idx = None
        self.phase = "main"
        self._clear_column_highlight()
        self._set_status("⚔ Ход игрока завершён...")

        self.engine.attack_phase("player")
        self.engine.advance_phase()
        over = self.engine.check_game_over()
        if over:
            self._game_over(over)
            return

        self.engine.enemy_turn()
        over = self.engine.check_game_over()
        if over:
            self._game_over(over)
            return

        self.engine.turn_number += 1
        self._start_player_turn()
        self._set_status(f"Ход {self.engine.turn_number}. Выберите карту (1-4)")
        self._refresh_all()

    def _game_over(self, winner: str):
        """Показать экран Game Over."""
        self.engine.update_stats()
        self.phase = "game_over"

        level_name = self.engine.state.level_config.get("name", "Unknown")
        stats = dict(self.engine.state.stats)

        def handle_game_over(result):
            if result == "restart":
                self._restart_level()
            elif result == "next":
                self._next_level()
            elif result == "quit":
                self.action_quit()

        self.push_screen(
            GameOverScreen(winner, level_name, stats, self.current_level),
            callback=handle_game_over,
        )

    def _restart_level(self):
        """Перезапустить текущий уровень."""
        self.engine = self._create_engine()
        self.selected_hand_idx = None
        self.phase = "main"
        self.cursor_row = 0
        self.cursor_col = 0
        self._start_player_turn()
        self._refresh_all()
        self._set_status("🔄 Рестарт! Добро пожаловать на уровень заново.")

    def _next_level(self):
        """Перейти на следующий уровень."""
        self.current_level += 1
        if self.current_level >= total_levels():
            # Все уровни пройдены — вернуться на первый как супер-победу
            self._set_status("🎉 Все уровни пройдены! Начинаем снова...")
            self.current_level = 0
        self.engine = self._create_engine()
        self.selected_hand_idx = None
        self.phase = "main"
        self.cursor_row = 0
        self.cursor_col = 0
        self._start_player_turn()
        self._refresh_all()
        self._set_status(f"🏔 Следующий уровень: {self.engine.state.level_config.get('name', 'Unknown')}")
        self._clear_column_highlight()

    # ─── cursor ─────────────────────────────────────────

    def action_cursor_up(self):
        if self.phase == "game_over":
            return
        self.cursor_row = max(0, self.cursor_row - 1)
        self._refresh_cursor()
        self._refresh_column_highlight()
        self._refresh_info()

    def action_cursor_down(self):
        if self.phase == "game_over":
            return
        self.cursor_row = min(3, self.cursor_row + 1)
        self._refresh_cursor()
        self._refresh_column_highlight()
        self._refresh_info()

    def action_cursor_left(self):
        if self.phase == "game_over":
            return
        self.cursor_col = max(0, self.cursor_col - 1)
        self._refresh_cursor()
        self._refresh_column_highlight()
        self._refresh_info()

    def action_cursor_right(self):
        if self.phase == "game_over":
            return
        self.cursor_col = min(4, self.cursor_col + 1)
        self._refresh_cursor()
        self._refresh_column_highlight()
        self._refresh_info()

    def action_show_info(self):
        self._refresh_info()

    # ─── quit ───────────────────────────────────────────

    def action_quit(self):
        save_game("save_placeholder.json", {"state": "placeholder"})
        self.exit()


# ─── entry point ────────────────────────────────────────


def run_app():
    app = FungiBattleApp()
    app.run()


if __name__ == "__main__":
    run_app()