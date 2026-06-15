from typing import Optional, List
from dataclasses import dataclass, field
from .card import Card


@dataclass
class Cell:
    owner: Optional[str] = None  # 'player' | 'enemy' | None
    card: Optional[Card] = None
    row: int = 0
    col: int = 0
    prepared: bool = False


@dataclass
class Board:
    width: int = 5
    height: int = 4
    grid: List[List[Cell]] = field(default_factory=list)

    def __post_init__(self):
        if not self.grid:
            self.grid = [
                [Cell(owner=None, card=None, row=r, col=c) for c in range(self.width)]
                for r in range(self.height)
            ]

    def cell(self, row: int, col: int) -> Cell:
        return self.grid[row][col]


@dataclass
class PlayerState:
    hp: int = 20
    gold: int = 3
    deck: Optional[object] = None
    hand: List[Card] = field(default_factory=list)
    discard: List[Card] = field(default_factory=list)


@dataclass
class GameState:
    board: Board = field(default_factory=Board)
    player: PlayerState = field(default_factory=PlayerState)
    enemy: PlayerState = field(default_factory=PlayerState)
    turn_owner: str = "player"  # 'player' or 'enemy'
    turn_number: int = 1
    rng_seed: int = 0
    level_config: dict = field(default_factory=dict)
    level_index: int = 0
    stats: dict = field(default_factory=lambda: {
        "cards_played": 0,
        "damage_dealt": 0,
        "gold_earned": 0,
        "turns_survived": 0,
    })
