"""Тесты прогрессии уровней через GameEngine."""
import pytest
from game.engine import GameEngine
from game.levels import total_levels, get_level, LEVELS


def test_all_levels_create_valid_engines():
    """Для каждого уровня можно создать движок."""
    for i in range(total_levels()):
        e = GameEngine.create_for_level(i, seed=42)
        cfg = get_level(i)
        assert e.state.player.hp == cfg["player_hp"]
        assert e.state.enemy.hp == cfg["enemy_hp"]
        assert e.state.level_index == i


def test_last_level_works():
    """Последний уровень тоже работает."""
    last = total_levels() - 1
    e = GameEngine.create_for_level(last, seed=42)
    assert e.state.level_index == last
    assert e.state.player.hp > 0
    assert e.state.enemy.hp > 0


def test_level_uses_correct_ai_difficulty():
    """Каждый уровень создаёт AI соответствующей сложности."""
    for i in range(total_levels()):
        e = GameEngine.create_for_level(i, seed=42)
        cfg = get_level(i)
        assert e.ai.difficulty == cfg["ai_difficulty"]


def test_engines_are_independent():
    """Два движка от одних сидов не разделяют состояние."""
    e1 = GameEngine.create_for_level(0, seed=42)
    e2 = GameEngine.create_for_level(0, seed=42)
    e1.state.player.hp = 1
    assert e2.state.player.hp == get_level(0)["player_hp"]


def test_engine_repr_safe():
    """Создание движка не падает при level_config=None."""
    e = GameEngine(seed=42, level_config=None)
    assert e.state.player.hp == 20
    assert e.state.enemy.hp == 20
