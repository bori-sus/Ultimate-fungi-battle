"""Тесты загрузки карт."""
import os
from game.card_loader import load_cards, build_deck_from_cards
from game.card import Card


CARDS_JSON = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "cards.json"
)


def test_load_cards_returns_list():
    cards = load_cards(CARDS_JSON)
    assert isinstance(cards, list)
    assert len(cards) > 0


def test_all_cards_are_card_instances():
    cards = load_cards(CARDS_JSON)
    assert all(isinstance(c, Card) for c in cards)


def test_cards_have_unique_ids():
    cards = load_cards(CARDS_JSON)
    ids = [c.id for c in cards]
    assert len(set(ids)) == len(ids), "duplicate card ids found"


def test_cards_have_valid_stats():
    cards = load_cards(CARDS_JSON)
    for c in cards:
        assert c.cost >= 1
        assert c.atk >= 0
        assert c.hp >= 1
        assert c.max_hp >= c.hp


def test_cards_have_names():
    cards = load_cards(CARDS_JSON)
    for c in cards:
        assert c.name and c.name.strip()


def test_build_deck_default_size():
    cards = load_cards(CARDS_JSON)
    deck = build_deck_from_cards(cards, deck_size=30, seed=1)
    assert len(deck) == 30


def test_build_deck_with_cost_filter():
    cards = load_cards(CARDS_JSON)
    deck = build_deck_from_cards(cards, deck_size=10, seed=1, cost_filter=(1, 2))
    assert len(deck) == 10
    assert all(1 <= c.cost <= 2 for c in deck)


def test_build_deck_is_shuffled_with_seed():
    cards = load_cards(CARDS_JSON)
    d1 = build_deck_from_cards(cards, deck_size=20, seed=42)
    d2 = build_deck_from_cards(cards, deck_size=20, seed=42)
    assert [c.id for c in d1] == [c.id for c in d2]


def test_build_deck_differs_with_different_seeds():
    cards = load_cards(CARDS_JSON)
    d1 = build_deck_from_cards(cards, deck_size=20, seed=1)
    d2 = build_deck_from_cards(cards, deck_size=20, seed=2)
    # на 20 картах перестановки почти наверняка отличаются
    assert [c.id for c in d1] != [c.id for c in d2]
