"""Тесты игрового движка (engine.py)."""
import pytest
from game.engine import GameEngine
from game.card import Card
from game.deck import Deck
from game.levels import get_level, total_levels


# ─── helpers ────────────────────────────────────────────


def _make_engine(level_index: int = 0, seed: int = 42) -> GameEngine:
    return GameEngine.create_for_level(level_index, seed=seed)


# ─── init / lifecycle ───────────────────────────────────


def test_engine_creation():
    e = _make_engine()
    assert e.turn_number == 1
    assert e.state.player.hp > 0
    assert e.state.enemy.hp > 0
    assert e.state.board.width == 5
    assert e.state.board.height == 4


def test_engine_initial_hand_drawn():
    e = _make_engine()
    # после _initial_draws() — 3 карты у каждого
    assert len(e.state.player.hand) == 3
    assert len(e.state.enemy.hand) == 3


def test_engine_gold_at_start():
    e = _make_engine()
    # start_gold из конфига уровня
    cfg = e.state.level_config
    assert e.state.player.gold == cfg.get("start_gold", 3)


def test_create_for_level_uses_level_config():
    """create_for_level подставляет HP/золото/etc из конфига уровня."""
    e0 = _make_engine(0)
    cfg0 = get_level(0)
    assert e0.state.player.hp == cfg0["player_hp"]
    assert e0.state.enemy.hp == cfg0["enemy_hp"]
    assert e0.state.player.gold == cfg0["start_gold"]
    assert e0.state.level_index == 0


def test_create_for_different_levels():
    """Разные уровни дают разные HP/золото."""
    e0 = _make_engine(0)
    e1 = _make_engine(1)
    assert e0.state.player.hp != e1.state.player.hp or e0.state.enemy.hp != e1.state.enemy.hp


def test_hand_max_constant():
    e = _make_engine()
    assert e.HAND_MAX == 4


# ─── begin_turn ─────────────────────────────────────────


def test_begin_turn_first_player():
    e = _make_engine()
    e.state.player.gold = 0
    e.begin_turn("player")
    cfg = e.state.level_config
    # первый ход — устанавливается start_gold
    assert e.state.player.gold == cfg.get("start_gold", 3)


def test_begin_turn_increases_gold():
    e = _make_engine()
    # turn_number > 1 => +gold_per_turn
    e.turn_number = 2
    e.state.player.gold = 5
    e.begin_turn("player")
    cfg = e.state.level_config
    assert e.state.player.gold == 5 + cfg.get("gold_per_turn", 1)


def test_begin_turn_draws_card():
    e = _make_engine()
    e.state.player.hand = []  # обнулим руку
    e.begin_turn("player")
    assert len(e.state.player.hand) >= 1


def test_begin_turn_enemy():
    e = _make_engine()
    e.turn_number = 2
    e.state.enemy.gold = 0
    e.begin_turn("enemy")
    cfg = e.state.level_config
    # не первый ход — прибавляем gold_per_turn
    assert e.state.enemy.gold == cfg.get("gold_per_turn", 1)


# ─── play_card_by_id ────────────────────────────────────


def test_play_card_by_id_success():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    e.state.player.gold = 10
    initial_hand_size = len(e.state.player.hand)
    card_id = e.state.player.hand[0].id
    bottom = e.state.board.height - 1
    ok = e.play_card_by_id("player", card_id, 0)
    assert ok
    assert e.state.board.cell(bottom, 0).card is not None
    assert len(e.state.player.hand) == initial_hand_size - 1  # карта убрана из руки


def test_play_card_by_id_insufficient_gold():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    card = e.state.player.hand[0]
    e.state.player.gold = 0  # нет золота
    ok = e.play_card_by_id("player", card.id, 0)
    assert not ok
    # карта осталась в руке
    assert card in e.state.player.hand


def test_play_card_by_id_occupied_cell():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    e.state.player.gold = 100
    card = e.state.player.hand[0]
    # занимаем клетку
    bottom = e.state.board.height - 1
    blocker = Card(id="block", name="B", cost=0, atk=0, hp=1, max_hp=1)
    e.state.board.cell(bottom, 2).card = blocker
    ok = e.play_card_by_id("player", card.id, 2)
    assert not ok


def test_play_card_by_id_invalid_column():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    e.state.player.gold = 100
    card = e.state.player.hand[0]
    ok = e.play_card_by_id("player", card.id, 99)  # вне доски
    assert not ok


def test_play_card_by_id_unknown_card():
    e = _make_engine()
    e.state.player.gold = 100
    ok = e.play_card_by_id("player", "nonexistent_id", 0)
    assert not ok


def test_play_card_deducts_gold():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    card = e.state.player.hand[0]
    e.state.player.gold = 10
    cost = card.cost
    e.play_card_by_id("player", card.id, 0)
    assert e.state.player.gold == 10 - cost


def test_play_card_stats_updated():
    e = _make_engine()
    e.state.player.gold = 100
    # поймаем первую попавшуюся карту
    for card in e.state.player.hand:
        if card.cost <= 100:
            e.play_card_by_id("player", card.id, 0)
            assert e.state.stats["cards_played"] == 1
            assert e.state.stats["gold_earned"] == card.cost
            return
    pytest.skip("no affordable card")


def test_play_enemy_card():
    e = _make_engine()
    if not e.state.enemy.hand:
        pytest.skip("no enemy card")
    e.state.enemy.gold = 100
    card = e.state.enemy.hand[0]
    ok = e.play_card_by_id("enemy", card.id, 0)
    assert ok
    assert e.state.board.cell(0, 0).card is not None


# ─── sell_from_hand ─────────────────────────────────────


def test_sell_from_hand_returns_gold():
    e = _make_engine()
    e.state.player.gold = 0
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    card = e.state.player.hand[0]
    cost = card.cost
    ok = e.sell_from_hand("player", 0)
    assert ok
    # получили floor(cost/2)
    expected_gain = cost // 2
    assert e.state.player.gold == expected_gain


def test_sell_from_hand_invalid_index():
    e = _make_engine()
    ok = e.sell_from_hand("player", 99)
    assert not ok


def test_sell_moves_to_discard():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    card = e.state.player.hand[0]
    e.sell_from_hand("player", 0)
    assert card in e.state.player.discard


# ─── attack_phase ───────────────────────────────────────


def test_attack_phase_face_damage():
    """Если есть готовая карта и напротив пусто — урон лицу."""
    e = _make_engine()
    e.state.player.hand = []
    e.state.player.discard = []
    # ставим готовую карту игрока на подготовленный ряд
    p_prepared = e.state.board.height - 2  # row 2
    p = Card(id="atk1", name="A1", cost=2, atk=3, hp=2, max_hp=2)
    e.state.board.cell(p_prepared, 0).card = p
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    # на пути врага — пусто
    enemy_hp_before = e.state.enemy.hp
    e.attack_phase("player")
    # урон 3 лицу врага
    assert e.state.enemy.hp == enemy_hp_before - 3


def test_attack_phase_blocked_by_enemy():
    """Если напротив есть готовая карта врага — атакуем её, не лицо."""
    e = _make_engine()
    p_prepared = e.state.board.height - 2  # row 2
    e_prepared = 1  # row 1
    p = Card(id="atk1", name="A1", cost=2, atk=3, hp=2, max_hp=2)
    e_card = Card(id="def1", name="D1", cost=2, atk=1, hp=5, max_hp=5)
    e.state.board.cell(p_prepared, 0).card = p
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    e.state.board.cell(e_prepared, 0).card = e_card
    e.state.board.cell(e_prepared, 0).owner = "enemy"
    e.state.board.cell(e_prepared, 0).prepared = True
    enemy_hp_before = e.state.enemy.hp
    e.attack_phase("player")
    # лицо не пострадало
    assert e.state.enemy.hp == enemy_hp_before
    # у вражеской карты -3 HP
    assert e.state.board.cell(e_prepared, 0).card.hp == 5 - 3


def test_attack_phase_destroys_card():
    e = _make_engine()
    p_prepared = e.state.board.height - 2
    e_prepared = 1
    p = Card(id="atk1", name="A1", cost=2, atk=10, hp=2, max_hp=2)
    e_card = Card(id="def1", name="D1", cost=2, atk=1, hp=2, max_hp=2)
    e.state.board.cell(p_prepared, 0).card = p
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    e.state.board.cell(e_prepared, 0).card = e_card
    e.state.board.cell(e_prepared, 0).owner = "enemy"
    e.state.board.cell(e_prepared, 0).prepared = True
    e.attack_phase("player")
    # вражеская карта уничтожена
    assert e.state.board.cell(e_prepared, 0).card is None
    # и ушла в сброс
    assert e_card in e.state.enemy.discard


def test_attack_phase_kills_attacker_via_spiky():
    """Эффект spiky у защитника — атакующий получает ответный урон."""
    e = _make_engine()
    p_prepared = e.state.board.height - 2
    e_prepared = 1
    p = Card(id="atk1", name="A1", cost=2, atk=2, hp=5, max_hp=5)
    e_card = Card(id="spiky", name="Spiky", cost=2, atk=0, hp=2, max_hp=2, effect_id="spiky")
    e.state.board.cell(p_prepared, 0).card = p
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    e.state.board.cell(e_prepared, 0).card = e_card
    e.state.board.cell(e_prepared, 0).owner = "enemy"
    e.state.board.cell(e_prepared, 0).prepared = True
    e.attack_phase("player")
    # атакующий потерял 1 HP
    assert p.hp == 5 - 1


# ─── advance_phase ──────────────────────────────────────


def test_advance_phase_moves_card_up():
    """Карта с row 3 должна перейти на row 2 (prepared)."""
    e = _make_engine()
    bottom = e.state.board.height - 1
    p_prepared = e.state.board.height - 2
    c = Card(id="c", name="C", cost=1, atk=1, hp=1, max_hp=1)
    e.state.board.cell(bottom, 2).card = c
    e.state.board.cell(bottom, 2).owner = "player"
    e.advance_phase()
    # карта переместилась на подготовленный ряд
    assert e.state.board.cell(p_prepared, 2).card is c
    assert e.state.board.cell(p_prepared, 2).prepared is True
    # исходная клетка пуста
    assert e.state.board.cell(bottom, 2).card is None


def test_advance_phase_enemy_moves_down():
    """Карта врага с row 0 должна перейти на row 1 (prepared)."""
    e = _make_engine()
    e_prepared = 1
    c = Card(id="c", name="C", cost=1, atk=1, hp=1, max_hp=1)
    e.state.board.cell(0, 2).card = c
    e.state.board.cell(0, 2).owner = "enemy"
    e.advance_phase()
    assert e.state.board.cell(e_prepared, 2).card is c
    assert e.state.board.cell(e_prepared, 2).prepared is True
    assert e.state.board.cell(0, 2).card is None


def test_advance_phase_does_not_move_prepared_card():
    """Prepared-карта не двигается."""
    e = _make_engine()
    p_prepared = e.state.board.height - 2
    c = Card(id="c", name="C", cost=1, atk=1, hp=1, max_hp=1)
    e.state.board.cell(p_prepared, 0).card = c
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    e.advance_phase()
    # карта на месте
    assert e.state.board.cell(p_prepared, 0).card is c


# ─── check_game_over ─────────────────────────────────────


def test_check_game_over_player_dead():
    e = _make_engine()
    e.state.player.hp = 0
    assert e.check_game_over() == "enemy"


def test_check_game_over_enemy_dead():
    e = _make_engine()
    e.state.enemy.hp = 0
    assert e.check_game_over() == "player"


def test_check_game_over_both_alive():
    e = _make_engine()
    assert e.check_game_over() is None


# ─── enemy_turn ──────────────────────────────────────────


def test_enemy_turn_runs_without_crash():
    e = _make_engine()
    e.enemy_turn()
    # после хода врага что-то поменялось (золото и т.д.)
    # главное — не было падения


def test_enemy_turn_plays_card():
    """Если у врага есть доступные карты — он их сыграет."""
    e = _make_engine()
    e.state.enemy.gold = 100  # много золота
    e.enemy_turn()
    # на доске должна быть хотя бы одна вражеская карта
    enemy_cards = []
    for r in range(e.state.board.height):
        for c in range(e.state.board.width):
            cell = e.state.board.cell(r, c)
            if cell.owner == "enemy" and cell.card is not None:
                enemy_cards.append(cell.card)
    assert len(enemy_cards) >= 1


# ─── stats ───────────────────────────────────────────────


def test_stats_initialized():
    e = _make_engine()
    assert e.state.stats["cards_played"] == 0
    assert e.state.stats["damage_dealt"] == 0
    assert e.state.stats["gold_earned"] == 0
    assert e.state.stats["turns_survived"] == 0


def test_update_stats_sets_turns():
    e = _make_engine()
    e.turn_number = 7
    e.update_stats()
    assert e.state.stats["turns_survived"] == 7


def test_damage_dealt_tracked_in_attack():
    e = _make_engine()
    p_prepared = e.state.board.height - 2
    p = Card(id="atk", name="Atk", cost=2, atk=4, hp=2, max_hp=2)
    e.state.board.cell(p_prepared, 0).card = p
    e.state.board.cell(p_prepared, 0).owner = "player"
    e.state.board.cell(p_prepared, 0).prepared = True
    e.attack_phase("player")
    assert e.state.stats["damage_dealt"] == 4


# ─── hand accessors ──────────────────────────────────────


def test_hand_card_ids():
    e = _make_engine()
    ids = e.hand_card_ids("player")
    assert isinstance(ids, list)
    assert all(isinstance(i, str) for i in ids)
    assert len(ids) == len(e.state.player.hand)


def test_hand_card_at():
    e = _make_engine()
    if not e.state.player.hand:
        pytest.skip("no card in hand")
    c = e.hand_card_at("player", 0)
    assert c is not None
    # вне диапазона
    assert e.hand_card_at("player", 99) is None


# ─── full smoke test ────────────────────────────────────


def test_full_turn_smoke():
    """Симулируем полный ход — всё должно работать без crash."""
    e = _make_engine()
    e.state.player.gold = 100
    # сыграть карту
    if e.state.player.hand:
        e.play_card_by_id("player", e.state.player.hand[0].id, 0)
    # ход врага
    e.enemy_turn()
    # проверить состояние
    assert e.check_game_over() is None or e.check_game_over() in ("player", "enemy")
