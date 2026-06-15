import random
from typing import List
from .card import Card


class Deck:
    def __init__(self, cards: List[Card] = None, seed: int = None):
        self.seed = seed
        self._rng = random.Random(seed)
        self.cards = list(cards) if cards else []
        self.discard: List[Card] = []

    def shuffle(self):
        self._rng.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            self._reshuffle_discard()
        if not self.cards:
            raise IndexError("Deck and discard are empty")
        return self.cards.pop()

    def _reshuffle_discard(self):
        self.cards = list(self.discard)
        self.discard = []
        self.shuffle()

    def add_to_discard(self, card: Card):
        self.discard.append(card)

    def add_card(self, card: Card):
        self.cards.append(card)

    def __len__(self):
        return len(self.cards)
