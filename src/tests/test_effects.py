"""Тесты системы эффектов."""
import pytest
from game.engine import GameEngine
from game.effects import EFFECT_REGISTRY, apply_effect
from game.card import Card


# ─── registry ───────────────────────────────────────────


def test_registry_has_basic_effects():
    """Базовые эффекты должны быть зарегистрированы."""
    expected = ["glow", "heal1", "heal2", "gold", "gold3",
                "poison", "deadly_poison", "fortify", "swift",
                "drain", "spiky", "double_strike", "taunt",
                "stink", "growth", "spores"]
    for eid in expected:
        assert eid in EFFECT_REGISTRY, f"effect {eid} not registered"


def test_apply_effect_unknown_returns_none():
    result = apply_effect("nonexistent_effect", None, "player", "x", "deploy")
    assert result is None


def test_apply_effect_known_returns_dict_or_none():
    """Применение известного эффекта — возвращает dict или None, не падает."""
    e = GameEngine.create_for_level(0, seed=1)
    result = apply_effect("glow", e, "player", "x", "deploy")
    # glow возвращает None (модифицирует состояние, не возвращает словарь)
    assert result is None or isinstance(result, dict)


# ─── glow ───────────────────────────────────────────────


def test_glow_deals_face_damage():
    e = GameEngine.create_for_level(0, seed=1)
    before = e.state.enemy.hp
    apply_effect("glow", e, "player", "x", "deploy")
    assert e.state.enemy.hp == before - 1


def test_glow_does_nothing_on_other_events():
    e = GameEngine.create_for_level(0, seed=1)
    before = e.state.enemy.hp
    apply_effect("glow", e, "player", "x", "attack")
    assert e.state.enemy.hp == before  # без изменений


# ─── heal ───────────────────────────────────────────────


def test_heal1_heals_player():
    e = GameEngine.create_for_level(0, seed=1)
    e.state.player.hp = 10
    apply_effect("heal1", e, "player", "x", "deploy")
    assert e.state.player.hp == 11


def test_heal2_heals_player():
    e = GameEngine.create_for_level(0, seed=1)
    e.state.player.hp = 10
    apply_effect("heal2", e, "player", "x", "deploy")
    assert e.state.player.hp == 12


def test_heal_caps_at_99():
    e = GameEngine.create_for_level(0, seed=1)
    e.state.player.hp = 99
    apply_effect("heal2", e, "player", "x", "deploy")
    assert e.state.player.hp == 99  # не больше 99


# ─── gold ───────────────────────────────────────────────


def test_gold_gives_1_gold():
    e = GameEngine.create_for_level(0, seed=1)
    e.state.player.gold = 5
    apply_effect("gold", e, "player", "x", "deploy")
    assert e.state.player.gold == 6


def test_gold3_gives_3_gold():
    e = GameEngine.create_for_level(0, seed=1)
    e.state.player.gold = 5
    apply_effect("gold3", e, "player", "x", "deploy")
    assert e.state.player.gold == 8


# ─── poison ─────────────────────────────────────────────


def test_poison_adds_extra_damage():
    result = apply_effect("poison", None, "player", "x", "attack")
    assert result == {"extra_damage": 1}


def test_deadly_poison_adds_2_damage():
    result = apply_effect("deadly_poison", None, "player", "x", "attack")
    assert result == {"extra_damage": 2}


def test_poison_no_modifier_on_other_events():
    result = apply_effect("poison", None, "player", "x", "deploy")
    assert result is None


# ─── drain ──────────────────────────────────────────────


def test_drain_returns_drain_true():
    result = apply_effect("drain", None, "player", "x", "attack")
    assert result == {"drain": True}


# ─── double_strike ──────────────────────────────────────


def test_double_strike_on_attack():
    result = apply_effect("double_strike", None, "player", "x", "attack")
    assert result == {"double_strike": True}


# ─── taunt ──────────────────────────────────────────────


def test_taunt_returns_dict_on_attack():
    result = apply_effect("taunt", None, "player", "x", "attack")
    assert result == {"taunt": True}


# ─── fortify ────────────────────────────────────────────


def test_fortify_increases_stats():
    e = GameEngine.create_for_level(0, seed=1)
    p_prepared = e.state.board.height - 2
    c = Card(id="fort", name="Fort", cost=1, atk=2, hp=2, max_hp=2, effect_id="fortify")
    e.state.board.cell(p_prepared, 0).card = c
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    apply_effect("fortify", e, "player", "fort", "prepare")
    assert c.atk == 3
    assert c.hp == 3
    assert c.max_hp == 3


# ─── stink ──────────────────────────────────────────────


def test_stink_reduces_enemy_atk():
    e = GameEngine.create_for_level(0, seed=1)
    e_prepared = 1
    enemy_card = Card(id="e", name="E", cost=1, atk=3, hp=2, max_hp=2)
    e.state.board.cell(e_prepared, 0).card = enemy_card
    e.state.board.cell(e_prepared, 0).owner = "enemy"
    e.state.board.cell(e_prepared, 0).prepared = True
    apply_effect("stink", e, "player", "s", "prepare")
    assert enemy_card.atk == 2


def test_stink_does_not_below_zero():
    e = GameEngine.create_for_level(0, seed=1)
    e_prepared = 1
    enemy_card = Card(id="e", name="E", cost=1, atk=0, hp=2, max_hp=2)
    e.state.board.cell(e_prepared, 0).card = enemy_card
    e.state.board.cell(e_prepared, 0).owner = "enemy"
    e.state.board.cell(e_prepared, 0).prepared = True
    apply_effect("stink", e, "player", "s", "prepare")
    assert enemy_card.atk == 0  # не уходит в минус


# ─── growth ─────────────────────────────────────────────


def test_growth_increases_prepared_card():
    e = GameEngine.create_for_level(0, seed=1)
    p_prepared = e.state.board.height - 2
    c = Card(id="g", name="G", cost=1, atk=2, hp=2, max_hp=2, effect_id="growth")
    e.state.board.cell(p_prepared, 0).card = c
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    apply_effect("growth", e, "player", "g", "turn_start")
    assert c.atk == 3
    assert c.hp == 3
    assert c.max_hp == 3


# ─── spores ─────────────────────────────────────────────


def test_spores_deals_face_damage_on_death():
    e = GameEngine.create_for_level(0, seed=1)
    before = e.state.enemy.hp
    apply_effect("spores", e, "player", "x", "death")
    assert e.state.enemy.hp == before - 2


# ─── swift ──────────────────────────────────────────────


def test_swift_makes_card_prepared_on_deploy():
    e = GameEngine.create_for_level(0, seed=1)
    bottom = e.state.board.height - 1
    p_prepared = e.state.board.height - 2
    c = Card(id="swift", name="Swift", cost=2, atk=2, hp=1, max_hp=1, effect_id="swift")
    e.state.board.cell(bottom, 0).card = c
    e.state.board.cell(bottom, 0).owner = "player"
    e.state.board.cell(bottom, 0).prepared = False
    apply_effect("swift", e, "player", "swift", "deploy")
    # карта теперь на prepared-ряду
    assert e.state.board.cell(p_prepared, 0).card is c
    assert e.state.board.cell(p_prepared, 0).prepared is True
