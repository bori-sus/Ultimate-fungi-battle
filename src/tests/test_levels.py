"""Тесты системы уровней."""
from game.levels import list_levels, total_levels, get_level, LEVELS


def test_total_levels_positive():
    assert total_levels() > 0


def test_list_levels_returns_all():
    levels = list_levels()
    assert len(levels) == total_levels()
    assert levels is LEVELS  # возвращаем тот же объект


def test_get_level_valid():
    lvl = get_level(0)
    assert "name" in lvl
    assert lvl["name"]  # не пустое


def test_get_level_out_of_bounds_returns_last():
    """Запрос несуществующего уровня — возвращаем последний (без crash)."""
    huge = 999
    lvl = get_level(huge)
    assert lvl is LEVELS[-1]


def test_level_required_fields():
    for i, lvl in enumerate(LEVELS):
        assert "name" in lvl, f"level {i} missing name"
        assert "player_hp" in lvl, f"level {i} missing player_hp"
        assert "enemy_hp" in lvl, f"level {i} missing enemy_hp"
        assert "start_gold" in lvl, f"level {i} missing start_gold"
        assert "gold_per_turn" in lvl, f"level {i} missing gold_per_turn"
        assert "ai_difficulty" in lvl, f"level {i} missing ai_difficulty"


def test_levels_have_increasing_difficulty():
    """Каждый следующий уровень не слабее предыдущего по HP врага."""
    for i in range(len(LEVELS) - 1):
        prev = LEVELS[i]
        cur = LEVELS[i + 1]
        assert cur["enemy_hp"] >= prev["enemy_hp"]


def test_levels_have_unique_names():
    names = [l["name"] for l in LEVELS]
    assert len(set(names)) == len(names)
