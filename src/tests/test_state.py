"""Тесты для моделей данных (state)."""
from game.state import Cell, Board, PlayerState, GameState
from game.card import Card


def test_cell_defaults():
    cell = Cell()
    assert cell.owner is None
    assert cell.card is None
    assert cell.row == 0
    assert cell.col == 0
    assert cell.prepared is False


def test_cell_with_values():
    c = Card(id="x", name="X", cost=1, atk=1, hp=1, max_hp=1)
    cell = Cell(owner="player", card=c, row=2, col=3, prepared=True)
    assert cell.owner == "player"
    assert cell.card is c
    assert cell.row == 2
    assert cell.col == 3
    assert cell.prepared is True


def test_board_defaults():
    board = Board()
    assert board.width == 5
    assert board.height == 4
    # 5×4 = 20 клеток, все пустые
    assert all(
        board.cell(r, c).owner is None and board.cell(r, c).card is None
        for r in range(board.height)
        for c in range(board.width)
    )


def test_board_cell_access():
    board = Board()
    cell = board.cell(2, 3)
    assert cell.row == 2
    assert cell.col == 3
    cell.owner = "player"
    assert board.cell(2, 3).owner == "player"


def test_player_state_defaults():
    p = PlayerState()
    assert p.hp == 20
    assert p.gold == 3
    assert p.deck is None
    assert p.hand == []
    assert p.discard == []


def test_game_state_defaults():
    g = GameState()
    assert g.board.width == 5
    assert g.board.height == 4
    assert g.turn_owner == "player"
    assert g.turn_number == 1
    assert g.rng_seed == 0
    assert g.level_config == {}
    assert g.level_index == 0
    assert g.stats["cards_played"] == 0
    assert g.stats["damage_dealt"] == 0
    assert g.stats["gold_earned"] == 0
    assert g.stats["turns_survived"] == 0


def test_game_state_stats_independent_per_instance():
    g1 = GameState()
    g2 = GameState()
    g1.stats["cards_played"] = 5
    assert g2.stats["cards_played"] == 0  # не разделяют dict


def test_board_grid_is_5x4():
    board = Board()
    assert len(board.grid) == 4
    for row in board.grid:
        assert len(row) == 5
