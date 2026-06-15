"""Система уровней с прогрессией.

Каждый уровень — dict с конфигурацией:
  name          — название
  player_hp     — HP игрока
  enemy_hp      — HP врага
  start_gold    — стартовое золото
  gold_per_turn — золото за ход
  enemy_costs   — диапазон стоимости карт врага (min, max) или None
  ai_difficulty — сложность AI
  description   — описание уровня
"""

LEVELS = [
    {
        "name": "Лесная опушка",
        "player_hp": 20,
        "enemy_hp": 20,
        "start_gold": 3,
        "gold_per_turn": 1,
        "enemy_costs": (1, 4),
        "ai_difficulty": "easy",
        "description": "Первая битва. Враг слаб, но коварен.",
    },
    {
        "name": "Гнилое болото",
        "player_hp": 20,
        "enemy_hp": 22,
        "start_gold": 3,
        "gold_per_turn": 1,
        "enemy_costs": (1, 4),
        "ai_difficulty": "easy",
        "description": "Туман стелется над водой. Враг сильнее.",
    },
    {
        "name": "Тёмная чаща",
        "player_hp": 22,
        "enemy_hp": 22,
        "start_gold": 4,
        "gold_per_turn": 1,
        "enemy_costs": (1, 5),
        "ai_difficulty": "easy",
        "description": "Деревья смыкаются над головой...",
    },
    {
        "name": "Грибница-лабиринт",
        "player_hp": 22,
        "enemy_hp": 24,
        "start_gold": 4,
        "gold_per_turn": 1,
        "enemy_costs": (1, 5),
        "ai_difficulty": "medium",
        "description": "Извилистые туннели полны спор.",
    },
    {
        "name": "Зал мицелия",
        "player_hp": 24,
        "enemy_hp": 26,
        "start_gold": 4,
        "gold_per_turn": 2,
        "enemy_costs": (1, 5),
        "ai_difficulty": "medium",
        "description": "Главный зал грибного королевства.",
    },
    {
        "name": "Трон спорового владыки",
        "player_hp": 25,
        "enemy_hp": 30,
        "start_gold": 5,
        "gold_per_turn": 2,
        "enemy_costs": (2, 5),
        "ai_difficulty": "hard",
        "description": "Финальная битва с властелином грибов!",
    },
]


def get_level(index: int) -> dict:
    """Вернуть конфигурацию уровня по индексу (с защитой от выхода за границы)."""
    return LEVELS[min(index, len(LEVELS) - 1)]


def list_levels() -> list:
    return LEVELS


def total_levels() -> int:
    return len(LEVELS)
