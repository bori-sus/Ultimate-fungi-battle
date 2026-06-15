"""
Система эффектов карт.

Каждый эффект — функция, принимающая:
  - engine: GameEngine
  - owner: 'player' | 'enemy'
  - card_id: str
  - event: str — 'deploy' | 'prepare' | 'attack' | 'death' | 'turn_start'

Функция эффекта может модифицировать engine.state или возвращать dict с
модификаторами (например, {'extra_damage': 1, 'heal': 2, 'gold': 1}).
"""

from typing import Optional, Dict, Any
from .state import GameState
from math import floor

EFFECT_REGISTRY = {}


def register(effect_id: str):
    """Декоратор для регистрации эффекта."""

    def _inner(func):
        EFFECT_REGISTRY[effect_id] = func
        return func

    return _inner


def apply_effect(effect_id: str, engine, owner: str, card_id: str, event: str) -> Optional[Dict[str, Any]]:
    """Применить эффект и вернуть модификаторы (или None)."""
    func = EFFECT_REGISTRY.get(effect_id)
    if func:
        return func(engine, owner, card_id, event)
    return None


# ─── эффекты ────────────────────────────────────────────


@register("glow")
def glow(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При постановке — 1 урона лицу врага."""
    if event == "deploy":
        target = "enemy" if owner == "player" else "player"
        p = engine.state.enemy if target == "enemy" else engine.state.player
        p.hp -= 1
    return None


@register("heal1")
def heal1(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При постановке — лечит игрока на 1 HP."""
    if event == "deploy":
        p = engine.state.player if owner == "player" else engine.state.enemy
        p.hp = min(p.hp + 1, 99)
    return None


@register("heal2")
def heal2(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При постановке — лечит игрока на 2 HP."""
    if event == "deploy":
        p = engine.state.player if owner == "player" else engine.state.enemy
        p.hp = min(p.hp + 2, 99)
    return None


@register("gold")
def gold(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При постановке — даёт 1 золото."""
    if event == "deploy":
        p = engine.state.player if owner == "player" else engine.state.enemy
        p.gold += 1
    return None


@register("gold3")
def gold3(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При постановке — даёт 3 золота."""
    if event == "deploy":
        p = engine.state.player if owner == "player" else engine.state.enemy
        p.gold += 3
    return None


@register("poison")
def poison(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При атаке — +1 дополнительного урона."""
    if event == "attack":
        return {"extra_damage": 1}
    return None


@register("deadly_poison")
def deadly_poison(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При атаке — +2 дополнительного урона."""
    if event == "attack":
        return {"extra_damage": 2}
    return None


@register("fortify")
def fortify(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При подготовке — +1/+1 к карте."""
    if event == "prepare":
        board = engine.state.board
        for r in range(board.height):
            for c in range(board.width):
                cell = board.cell(r, c)
                if cell.card and cell.card.id == card_id:
                    cell.card.atk += 1
                    cell.card.hp += 1
                    cell.card.max_hp += 1
                    return None
    return None


@register("swift")
def swift(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При постановке — карта ставится сразу в prepared-ряд."""
    if event == "deploy":
        board = engine.state.board
        prepared = board.height - 2 if owner == "player" else 1
        for c in range(board.width):
            cell = board.cell(prepared, c)
            if cell.card and cell.card.id == card_id:
                cell.prepared = True
                return None
        # also check bottom/top row
        placement = board.height - 1 if owner == "player" else 0
        for c in range(board.width):
            cell = board.cell(placement, c)
            if cell.card and cell.card.id == card_id:
                # move to prepared row if free
                dest = board.cell(prepared, c)
                if dest.card is None:
                    dest.card = cell.card
                    dest.owner = owner
                    dest.prepared = True
                    cell.card = None
                    cell.owner = None
                else:
                    cell.prepared = True
                return None
    return None


@register("drain")
def drain(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При атаке — лечит владельца на величину урона."""
    if event == "attack":
        return {"drain": True}
    return None


@register("spiky")
def spiky(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При получении урона — 1 ответного урона атакующему."""
    if event == "damaged":
        # engine will call this when card takes damage
        return {"retaliate": 1}
    return None


@register("double_strike")
def double_strike(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """Может атаковать дважды."""
    if event == "attack":
        return {"double_strike": True}
    return None


@register("taunt")
def taunt(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """Помечает карту как taunt — враг должен атаковать её первой."""
    if event == "prepare":
        return {"taunt": True}
    if event == "attack":
        return {"taunt": True}
    return None


@register("stink")
def stink(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При подготовке — вражеские prepared-карты теряют 1 ATK."""
    if event == "prepare":
        board = engine.state.board
        enemy_owner = "enemy" if owner == "player" else "player"
        for r in range(board.height):
            for c in range(board.width):
                cell = board.cell(r, c)
                if cell.card and cell.owner == enemy_owner and cell.prepared:
                    cell.card.atk = max(0, cell.card.atk - 1)
        return None
    return None


@register("growth")
def growth(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """В начале хода — +1/+1 если подготовлен."""
    if event == "turn_start":
        board = engine.state.board
        for r in range(board.height):
            for c in range(board.width):
                cell = board.cell(r, c)
                if cell.card and cell.card.id == card_id and cell.prepared and cell.owner == owner:
                    cell.card.atk += 1
                    cell.card.hp += 1
                    cell.card.max_hp += 1
                    return None
    return None


@register("spores")
def spores(engine, owner: str, card_id: str, event: str) -> Optional[Dict]:
    """При смерти — 2 урона лицу врага."""
    if event == "death":
        target = "enemy" if owner == "player" else "player"
        p = engine.state.enemy if target == "enemy" else engine.state.player
        p.hp -= 2
        return None
    return None
