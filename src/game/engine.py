from typing import List, Optional
from .state import GameState, Board, Cell
from .card import Card
from .deck import Deck
from .ai import AI
from .save import save_game
from .card_loader import load_cards, build_deck_from_cards
from .effects import apply_effect
from math import floor
import os


CARDS_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "cards.json")


class GameEngine:
    """Pure game logic — no I/O, usable from any UI (CLI, Textual, etc.)."""

    def __init__(self, seed: Optional[int] = None, level_config: Optional[dict] = None):
        self.state = GameState()
        # load cards from JSON
        all_cards = load_cards(CARDS_JSON)
        player_deck = build_deck_from_cards(all_cards, deck_size=30, seed=seed)

        lcfg = level_config or {}
        enemy_cost_min = lcfg.get("enemy_costs", (1, 4))[0]
        enemy_cost_max = lcfg.get("enemy_costs", (1, 4))[1]
        enemy_deck = build_deck_from_cards(
            all_cards, deck_size=30,
            seed=seed + 1 if seed is not None else None,
            cost_filter=(enemy_cost_min, enemy_cost_max),
        )

        self.state.player.deck = Deck(player_deck, seed=seed)
        self.state.enemy.deck = Deck(enemy_deck, seed=seed + 1 if seed is not None else None)

        self.HAND_MAX = 4
        self.state.level_config = lcfg
        self.state.player.hp = lcfg.get("player_hp", 20)
        self.state.enemy.hp = lcfg.get("enemy_hp", 20)
        # устанавливаем стартовое золото в обоих колодах сразу
        start_gold = lcfg.get("start_gold", 3)
        self.state.player.gold = start_gold
        self.state.enemy.gold = start_gold
        self.turn_number = 1
        ai_diff = lcfg.get("ai_difficulty", "easy")
        self.ai = AI(difficulty=ai_diff)
        self._effect_events: set = set()
        self._initial_draws()

    @classmethod
    def create_for_level(cls, level_index: int, seed: Optional[int] = None) -> "GameEngine":
        """Создать движок для указанного уровня."""
        from .levels import get_level
        lcfg = get_level(level_index)
        engine = cls(seed=seed, level_config=lcfg)
        engine.state.level_index = level_index
        return engine

    def _initial_draws(self):
        for _ in range(3):
            self.draw_phase("player")
            self.draw_phase("enemy")

    # ─── core game phases ────────────────────────────────

    def draw_phase(self, owner: str):
        p = self.state.player if owner == "player" else self.state.enemy
        try:
            card = p.deck.draw()
        except IndexError:
            return
        if len(p.hand) < self.HAND_MAX:
            p.hand.append(card)
        else:
            p.discard.append(card)

    def begin_turn(self, owner: str):
        cfg = self.state.level_config
        start = cfg.get("start_gold", 3)
        per = cfg.get("gold_per_turn", 1)
        p = self.state.player if owner == "player" else self.state.enemy
        if self.turn_number == 1 and owner == "player":
            p.gold = start
        elif self.turn_number == 1 and owner == "enemy":
            p.gold = start
        else:
            p.gold += per
        self.draw_phase(owner)
        # fire turn_start effects for this owner's prepared cards
        self._fire_board_effects(owner, "turn_start")

    def play_card_by_id(self, owner: str, card_id: str, column: int) -> bool:
        """Place a card from hand onto the board."""
        p = self.state.player if owner == "player" else self.state.enemy
        card = None
        idx = None
        for i, c in enumerate(p.hand):
            if c.id == card_id:
                card = c
                idx = i
                break
        if card is None:
            return False
        if p.gold < card.cost:
            return False
        if owner == "player":
            row = self.state.board.height - 1
        else:
            row = 0
        if column < 0 or column >= self.state.board.width:
            return False
        cell = self.state.board.cell(row, column)
        if cell.card is not None:
            return False
        p.gold -= card.cost
        cell.card = card
        cell.owner = owner
        cell.prepared = False
        p.hand.pop(idx)

        # track stats
        if owner == "player":
            self.state.stats["cards_played"] += 1
            self.state.stats["gold_earned"] += card.cost

        # fire deploy effect
        self._fire_effect(card.effect_id, owner, card.id, "deploy")

        # also fire deploy effects for swift (which may move card)
        if card.effect_id == "swift":
            self._fire_effect("swift", owner, card.id, "deploy")

        return True

    def sell_from_hand(self, owner: str, hand_index: int) -> bool:
        """Sell a card from hand for gold."""
        p = self.state.player if owner == "player" else self.state.enemy
        if hand_index < 0 or hand_index >= len(p.hand):
            return False
        card = p.hand.pop(hand_index)
        gain = floor(card.cost * 0.5)
        p.gold += gain
        p.discard.append(card)
        return True

    def attack_phase(self, owner: str):
        """Resolve all prepared card attacks for one side."""
        board = self.state.board
        height = board.height
        width = board.width
        direction = -1 if owner == "player" else 1
        face_target = "enemy" if owner == "player" else "player"

        # collect attacks with effect data
        # (attacker_cell, target_cell or None, effect_id)
        attacks = []
        for col in range(width):
            for row in range(height):
                cell = board.cell(row, col)
                if cell.card and cell.owner == owner and cell.prepared:
                    r = row + direction
                    target = None
                    while 0 <= r < height:
                        c2 = board.cell(r, col)
                        if c2.card and c2.owner != owner and c2.prepared:
                            target = c2
                            break
                        r += direction
                    attacks.append((cell, target, cell.card.effect_id))
                    break

        # ключ — (row, col), значение — (cell, damage)
        damage_map: dict = {}
        face_damage = {"player": 0, "enemy": 0}
        drain_heal = 0  # total drain healing for owner

        for attacker, target, effect_id in attacks:
            atk = attacker.card.atk
            atk_mods = self._fire_effect(effect_id, owner, attacker.card.id, "attack") or {}
            extra_damage = atk_mods.get("extra_damage", 0)
            effective_atk = atk + extra_damage

            if target:
                key = (target.row, target.col)
                if key not in damage_map:
                    damage_map[key] = [target, 0]
                damage_map[key][1] += effective_atk
                # drain
                if atk_mods.get("drain"):
                    drain_heal += effective_atk
                # retaliate (spiky) - check if target has retaliate
                if target.card and target.card.effect_id == "spiky":
                    # attacker takes 1 damage
                    attacker.card.hp -= 1
            else:
                face_damage[face_target] += effective_atk
                if atk_mods.get("drain"):
                    drain_heal += effective_atk

            # track stats for player attacks
            if owner == "player":
                self.state.stats["damage_dealt"] += effective_atk

            # double strike: attack again (same target or face)
            if atk_mods.get("double_strike") and target and target.card and target.card.hp > 0:
                # second attack
                if target:
                    key = (target.row, target.col)
                    if key not in damage_map:
                        damage_map[key] = [target, 0]
                    damage_map[key][1] += atk
                else:
                    face_damage[face_target] += atk
                if owner == "player":
                    self.state.stats["damage_dealt"] += atk

        # apply heal from drain
        if drain_heal > 0:
            p = self.state.player if owner == "player" else self.state.enemy
            p.hp = min(p.hp + drain_heal, 99)

        # apply damage to cells
        for _key, (target_cell, dmg) in damage_map.items():
            if target_cell.card is not None:
                target_cell.card.hp -= dmg

        # apply face damage
        if face_damage["player"]:
            self.state.player.hp -= face_damage["player"]
        if face_damage["enemy"]:
            self.state.enemy.hp -= face_damage["enemy"]

        # collect deaths + fire death effects
        for r in range(height):
            for c in range(width):
                cell = board.cell(r, c)
                if cell.card and cell.card.hp <= 0:
                    self._fire_effect(cell.card.effect_id, cell.owner or "", cell.card.id, "death")
                    owner_state = self.state.player if cell.owner == "player" else self.state.enemy
                    owner_state.discard.append(cell.card)
                    cell.card = None
                    cell.owner = None
                    cell.prepared = False

    def _fire_effect(self, effect_id, owner, card_id, event):
        if not effect_id:
            return None
        return apply_effect(effect_id, self, owner, card_id, event)

    def _fire_board_effects(self, owner: str, event: str):
        """Apply an event to all cards on board belonging to owner."""
        board = self.state.board
        for r in range(board.height):
            for c in range(board.width):
                cell = board.cell(r, c)
                if cell.card and cell.owner == owner:
                    self._fire_effect(cell.card.effect_id, owner, cell.card.id, event)

    def advance_phase(self):
        """Move non-prepared cards toward the prepared row."""
        board = self.state.board
        height = board.height
        width = board.width
        P_PREPARED = height - 2  # player prepared row
        E_PREPARED = 1           # enemy prepared row

        # build movement candidates
        player_moves = []
        enemy_moves = []
        ep = P_PREPARED
        for r in range(height):
            for c in range(width):
                cell = board.cell(r, c)
                if not cell.card or cell.prepared:
                    continue
                if cell.owner == "player" and r != ep:
                    dest = max(r - 1, 0)
                    if dest < ep:
                        dest = ep
                    if dest != r and board.cell(dest, c).card is None:
                        player_moves.append((r, c, dest, cell.card.id, cell.card.effect_id))
                elif cell.owner == "enemy" and r != E_PREPARED:
                    dest = min(r + 1, height - 1)
                    if dest > E_PREPARED:
                        dest = E_PREPARED
                    if dest != r and board.cell(dest, c).card is None:
                        enemy_moves.append((r, c, dest, cell.card.id, cell.card.effect_id))

        # apply player moves (top-down)
        for r, c, dest, cid, eff in sorted(player_moves, key=lambda m: m[0]):
            src = board.cell(r, c)
            dst = board.cell(dest, c)
            if src.card and dst.card is None:
                was_prepared = (dest == P_PREPARED)
                dst.card = src.card
                dst.owner = src.owner
                dst.prepared = was_prepared
                src.card = None
                src.owner = None
                src.prepared = False
                if was_prepared:
                    self._fire_effect(eff, "player", cid, "prepare")

        # apply enemy moves (bottom-up)
        for r, c, dest, cid, eff in sorted(enemy_moves, key=lambda m: m[0], reverse=True):
            src = board.cell(r, c)
            dst = board.cell(dest, c)
            if src.card and dst.card is None:
                was_prepared = (dest == E_PREPARED)
                dst.card = src.card
                dst.owner = src.owner
                dst.prepared = was_prepared
                src.card = None
                src.owner = None
                src.prepared = False
                if was_prepared:
                    self._fire_effect(eff, "enemy", cid, "prepare")

    def enemy_turn(self):
        """Run full AI enemy turn: begin, play, attack, advance."""
        self.begin_turn("enemy")
        moves = self.ai.take_turn(self.state)
        if moves:
            for card_id, col in moves:
                self.play_card_by_id("enemy", card_id, col)
        self.attack_phase("enemy")
        self.advance_phase()

    def update_stats(self):
        """Обновить статистику перед концом игры."""
        self.state.stats["turns_survived"] = self.turn_number

    def check_game_over(self) -> Optional[str]:
        if self.state.player.hp <= 0:
            return "enemy"
        if self.state.enemy.hp <= 0:
            return "player"
        return None

    def hand_card_ids(self, owner: str) -> List[str]:
        p = self.state.player if owner == "player" else self.state.enemy
        return [c.id for c in p.hand]

    def hand_card_at(self, owner: str, index: int) -> Optional[Card]:
        p = self.state.player if owner == "player" else self.state.enemy
        if 0 <= index < len(p.hand):
            return p.hand[index]
        return None