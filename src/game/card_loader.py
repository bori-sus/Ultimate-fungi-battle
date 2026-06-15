"""Загрузка карт из assets/cards.json."""

import json
import random
from typing import List, Optional
from .card import Card


def load_cards(path: str) -> List[Card]:
    """Загрузить список карт из JSON-файла."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = []
    for item in data:
        cards.append(Card(
            id=item["id"],
            name=item["name"],
            cost=item["cost"],
            atk=item["atk"],
            hp=item["hp"],
            max_hp=item["max_hp"],
            description=item.get("description", ""),
            ascii_top=item.get("ascii_top", ""),
            ascii_bottom=item.get("ascii_bottom", ""),
            tags=item.get("tags", None),
            persistent=item.get("persistent", False),
            effect_id=item.get("effect_id", None),
        ))
    return cards


def build_deck_from_cards(
    all_cards: List[Card],
    deck_size: int = 30,
    seed: Optional[int] = None,
    cost_filter: Optional[tuple] = None,
) -> List[Card]:
    """Собрать колоду из all_cards, выбрав deck_size карт.
    
    Если задан cost_filter=(min, max), выбираются только карты с cost в диапазоне.
    После выбора карты перемешиваются.
    """
    rng = random.Random(seed)
    pool = list(all_cards)
    if cost_filter:
        min_c, max_c = cost_filter
        pool = [c for c in pool if min_c <= c.cost <= max_c]
    if len(pool) < deck_size:
        # дублируем если не хватает
        pool = pool * (deck_size // len(pool) + 1)
    rng.shuffle(pool)
    return pool[:deck_size]