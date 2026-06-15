"""Тесты ИИ."""
import pytest
from game.ai import AI
from game.engine import GameEngine
from game.card import Card


def test_ai_creation():
    ai = AI()
    assert ai.difficulty == "easy"


def test_ai_creation_with_difficulty():
    ai = AI(difficulty="hard")
    assert ai.difficulty == "hard"


def test_ai_takes_turn_with_enough_gold():
    """Если у врага есть карты и золото — он сыграет хотя бы одну."""
    e = GameEngine.create_for_level(0, seed=1)
    e.state.enemy.gold = 100  # много золота
    # убедимся, что у врага есть карты
    assert len(e.state.enemy.hand) > 0
    moves = e.ai.take_turn(e.state)
    assert moves is not None
    assert len(moves) >= 1


def test_ai_takes_turn_with_no_gold():
    """Если у врага нет золота — он не сыграет ничего."""
    e = GameEngine.create_for_level(0, seed=1)
    e.state.enemy.gold = 0
    moves = e.ai.take_turn(e.state)
    # либо пустой список, либо None
    if moves is not None:
        assert len(moves) == 0


def test_ai_moves_reference_real_cards():
    """Все moves должны ссылаться на реальные карты в руке."""
    e = GameEngine.create_for_level(0, seed=1)
    e.state.enemy.gold = 100
    hand_ids = {c.id for c in e.state.enemy.hand}
    moves = e.ai.take_turn(e.state)
    if moves:
        for card_id, col in moves:
            assert card_id in hand_ids
            assert 0 <= col < e.state.board.width


def test_ai_does_not_exceed_gold():
    """AI не должен предлагать карты дороже, чем есть золота."""
    e = GameEngine.create_for_level(0, seed=1)
    gold = 5
    e.state.enemy.gold = gold
    moves = e.ai.take_turn(e.state) or []
    hand = {c.id: c for c in e.state.enemy.hand}
    for card_id, _ in moves:
        if card_id in hand:
            assert hand[card_id].cost <= gold


def test_ai_does_not_double_play_column():
    """AI не должен предлагать две карты в одну колонку за один ход."""
    e = GameEngine.create_for_level(0, seed=1)
    e.state.enemy.gold = 100
    moves = e.ai.take_turn(e.state) or []
    cols = [col for _, col in moves]
    assert len(cols) == len(set(cols))  # все колонки уникальны


def test_ai_uses_only_valid_columns():
    """Все колонки в moves должны быть в диапазоне 0..width-1."""
    e = GameEngine.create_for_level(0, seed=1)
    e.state.enemy.gold = 100
    moves = e.ai.take_turn(e.state) or []
    for _, col in moves:
        assert 0 <= col < e.state.board.width


def test_ai_actually_plays_cards():
    """Интеграционный тест: enemy_turn действительно ставит карты на доску."""
    e = GameEngine.create_for_level(0, seed=1)
    e.state.enemy.gold = 100
    e.enemy_turn()
    enemy_on_board = []
    for r in range(e.state.board.height):
        for c in range(e.state.board.width):
            cell = e.state.board.cell(r, c)
            if cell.owner == "enemy" and cell.card is not None:
                enemy_on_board.append(cell.card)
    assert len(enemy_on_board) >= 1
