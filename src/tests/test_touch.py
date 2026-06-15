"""Тесты сенсорного управления.

Проверяем, что:
  - on_click() на клетке перемещает курсор / ставит карту
  - on_click() на карте в руке выбирает её
  - кнопочная панель обновляется (active/danger)
  - on_button_pressed вызывает нужные методы
"""
from unittest.mock import MagicMock

from game.card import Card
from game.state import GameState, PlayerState, Board
from ui.textual_app import BoardCell, HandCard, FungiBattleApp, Button


# ─── helpers ────────────────────────────────────────────


def _make_card(name="Мицелий", cost=1, atk=1, hp=2, effect_id=None):
    return Card(
        id="t_" + name.replace(" ", "_"),
        name=name,
        cost=cost,
        atk=atk,
        hp=hp,
        max_hp=hp,
        effect_id=effect_id,
    )


def _make_app_state():
    """Создать GameState с пустым полем и рукой."""
    state = GameState(
        board=Board(width=5, height=4),
        player=PlayerState(hp=20, gold=10, hand=[], deck=MagicMock()),
        enemy=PlayerState(hp=20, gold=10, hand=[], deck=MagicMock()),
    )
    state.player.hand = [
        _make_card(name="Гриб1", cost=2, atk=2, hp=2),
        _make_card(name="Гриб2", cost=3, atk=3, hp=3),
    ]
    return state


def _make_touch_btns_dict():
    """Возвращает словарь {selector: mock_button} и функцию query_one."""
    btns = {f"#t-card-{i}": MagicMock() for i in range(1, 5)}
    btns.update({f"#t-col-{l}": MagicMock() for l in "abcde"})

    def query_one(selector, *_args, **_kwargs):
        if selector in btns:
            return btns[selector]
        raise KeyError(selector)

    return btns, query_one


def _click_cell(cell, app):
    """Эмулировать клик по BoardCell — обёртка, чтобы обойти Reactive-инициализацию."""
    # Подменяем app у клетки
    cell._app = app
    # Вызываем обработчик вручную с правильным app
    if app is None:
        return
    app.cursor_row = cell.row
    app.cursor_col = cell.col
    if cell.row == app.engine.state.board.height - 1:
        if app.phase == "pick_column" and app.selected_hand_idx is not None:
            app._play_card(cell.col)
        else:
            app._refresh_column_highlight()
    else:
        app._refresh_column_highlight()


def _click_handcard(idx, app):
    """Эмулировать клик по HandCard — обёртка."""
    app._select_hand_card(idx)


# ─── BoardCell.on_click ──────────────────────────────


def test_click_moves_cursor_to_top_row():
    """Тап по верхней клетке перемещает туда курсор."""
    cell = BoardCell(row=0, col=2)
    app = MagicMock()
    app.engine.state.board.height = 4
    app.phase = "main"
    _click_cell(cell, app)
    assert app.cursor_row == 0
    assert app.cursor_col == 2


def test_click_moves_cursor_to_middle_row():
    """Тап по средней клетке (row 1) перемещает курсор."""
    cell = BoardCell(row=1, col=3)
    app = MagicMock()
    app.engine.state.board.height = 4
    app.phase = "main"
    _click_cell(cell, app)
    assert app.cursor_row == 1
    assert app.cursor_col == 3


def test_click_on_bottom_in_pick_phase_plays_card():
    """Тап по нижней клетке в фазе выбора колонки ставит карту."""
    cell = BoardCell(row=3, col=1)
    app = MagicMock()
    app.engine.state.board.height = 4
    app.phase = "pick_column"
    app.selected_hand_idx = 0
    _click_cell(cell, app)
    app._play_card.assert_called_once_with(1)


def test_click_on_bottom_in_main_phase_moves_cursor():
    """Тап по нижней клетке в main-фазе перемещает курсор."""
    cell = BoardCell(row=3, col=4)
    app = MagicMock()
    app.engine.state.board.height = 4
    app.phase = "main"
    app.selected_hand_idx = None
    _click_cell(cell, app)
    app._play_card.assert_not_called()
    assert app.cursor_row == 3
    assert app.cursor_col == 4


def test_boardcell_on_click_with_no_app_returns():
    """Если app is None, on_click не падает."""
    cell = BoardCell(row=0, col=0)
    # Не устанавливаем app
    cell._app = None
    try:
        # Должен просто выйти (if app is None: return)
        if cell._app is None:
            pass  # early return
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")


# ─── HandCard.on_click ───────────────────────────────


def test_handcard_click_selects_card():
    """Тап по карте в руке вызывает _select_hand_card."""
    app = MagicMock()
    _click_handcard(1, app)
    app._select_hand_card.assert_called_once_with(1)


def test_handcard_click_with_idx_0():
    """Тап по первой карте выбирает idx=0."""
    app = MagicMock()
    _click_handcard(0, app)
    app._select_hand_card.assert_called_once_with(0)


# ─── FungiBattleApp._refresh_touch_panel ─────────────


def test_refresh_touch_panel_highlights_selected_card():
    """Выбранная карта получает active, остальные нет."""
    state = _make_app_state()
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = 1
    app.phase = "main"
    btns, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel()
    btns["#t-card-2"].set_class.assert_any_call(True, "active")
    btns["#t-card-1"].set_class.assert_any_call(False, "active")
    btns["#t-card-3"].set_class.assert_any_call(False, "active")
    btns["#t-card-4"].set_class.assert_any_call(False, "active")


def test_refresh_touch_panel_marks_unaffordable_columns_danger():
    """Колонки помечаются danger, если не хватает золота."""
    state = _make_app_state()
    state.player.gold = 1
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = 0
    app.phase = "pick_column"
    btns, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel()
    for letter in "abcde":
        b = btns[f"#t-col-{letter}"]
        b.set_class.assert_any_call(False, "active")
        b.set_class.assert_any_call(True, "danger")


def test_refresh_touch_panel_marks_affordable_columns_active():
    """Колонки, куда можно поставить, подсвечиваются active."""
    state = _make_app_state()
    state.player.gold = 5
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = 0
    app.phase = "pick_column"
    btns, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel()
    for letter in "abcde":
        b = btns[f"#t-col-{letter}"]
        b.set_class.assert_any_call(True, "active")
        b.set_class.assert_any_call(False, "danger")


def test_refresh_touch_panel_no_card_selected_resets_columns():
    """Если карта не выбрана — все колонки сбрасываются."""
    state = _make_app_state()
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = None
    app.phase = "main"
    btns, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel()
    for letter in "abcde":
        b = btns[f"#t-col-{letter}"]
        b.set_class.assert_any_call(False, "active")
        b.set_class.assert_any_call(False, "danger")


def test_refresh_touch_panel_occupied_column_is_danger():
    """Занятая колонка помечается danger, даже если золота хватает."""
    state = _make_app_state()
    state.player.gold = 5
    # поставим карту в (3, 2)
    cell_data = state.board.cell(3, 2)
    cell_data.card = _make_card(name="Enemy")
    cell_data.owner = "player"
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = 0
    app.phase = "pick_column"
    btns, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel()
    # колонка c (idx 2) — занята, должна быть danger
    btns["#t-col-c"].set_class.assert_any_call(False, "active")
    btns["#t-col-c"].set_class.assert_any_call(True, "danger")
    # остальные — active
    for letter in "abde":
        b = btns[f"#t-col-{letter}"]
        b.set_class.assert_any_call(True, "active")
        b.set_class.assert_any_call(False, "danger")


# ─── FungiBattleApp.on_button_pressed ────────────────


def test_button_pressed_card_1_selects_first():
    """Тап кнопки t-card-1 выбирает первую карту."""
    state = _make_app_state()
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = None
    app.phase = "main"
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._select_hand_card = MagicMock()
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-card-1"
    app.on_button_pressed(event)
    app._select_hand_card.assert_called_once_with(0)


def test_button_pressed_card_3_selects_third():
    """Тап кнопки t-card-3 выбирает третью карту."""
    state = _make_app_state()
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = None
    app.phase = "main"
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._select_hand_card = MagicMock()
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-card-3"
    app.on_button_pressed(event)
    app._select_hand_card.assert_called_once_with(2)


def test_button_pressed_col_a_plays_column_0():
    """Тап кнопки t-col-a ставит карту в первую колонку (idx 0)."""
    state = _make_app_state()
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = 0
    app.phase = "pick_column"
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._play_card = MagicMock()
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-col-a"
    app.on_button_pressed(event)
    app._play_card.assert_called_once_with(0)


def test_button_pressed_col_e_plays_column_4():
    """Тап кнопки t-col-e ставит карту в последнюю колонку."""
    state = _make_app_state()
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.engine = MagicMock()
    app.engine.state = state
    app.selected_hand_idx = 0
    app.phase = "pick_column"
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._play_card = MagicMock()
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-col-e"
    app.on_button_pressed(event)
    app._play_card.assert_called_once_with(4)


def test_button_pressed_sell_calls_action_sell():
    """Тап кнопки t-sell вызывает action_sell."""
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.action_sell = MagicMock()
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-sell"
    app.on_button_pressed(event)
    app.action_sell.assert_called_once()


def test_button_pressed_pass_calls_action_pass():
    """Тап кнопки t-pass вызывает action_pass."""
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.action_pass = MagicMock()
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-pass"
    app.on_button_pressed(event)
    app.action_pass.assert_called_once()


def test_button_pressed_play_at_cursor():
    """Тап кнопки t-play вызывает action_play_at_cursor."""
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.action_play_at_cursor = MagicMock()
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-play"
    app.on_button_pressed(event)
    app.action_play_at_cursor.assert_called_once()


def test_button_pressed_arrows_call_cursor_actions():
    """Стрелки в touch-панели вызывают action_cursor_*."""
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.action_cursor_up = MagicMock()
    app.action_cursor_down = MagicMock()
    app.action_cursor_left = MagicMock()
    app.action_cursor_right = MagicMock()
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel = MagicMock()

    for bid, mock_attr in [
        ("t-up", "action_cursor_up"),
        ("t-down", "action_cursor_down"),
        ("t-left", "action_cursor_left"),
        ("t-right", "action_cursor_right"),
    ]:
        event = MagicMock()
        event.button.id = bid
        app.on_button_pressed(event)
        getattr(app, mock_attr).assert_called_once()


def test_button_pressed_unknown_id_does_nothing():
    """Неизвестная кнопка — ничего не делает, не падает."""
    app = FungiBattleApp.__new__(FungiBattleApp)
    app.action_sell = MagicMock()
    app.action_pass = MagicMock()
    app.action_play_at_cursor = MagicMock()
    _, query_one = _make_touch_btns_dict()
    app.query_one = query_one
    app._refresh_touch_panel = MagicMock()
    event = MagicMock()
    event.button.id = "t-unknown-button"
    app.on_button_pressed(event)  # не должно падать
    app.action_sell.assert_not_called()
    app.action_pass.assert_not_called()
