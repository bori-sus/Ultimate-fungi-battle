"""Тесты для колоды."""
import pytest
from game.deck import Deck
from game.card import Card


def _make_card(cid: str) -> Card:
    return Card(id=cid, name=f"Card-{cid}", cost=1, atk=1, hp=1, max_hp=1)


def test_deck_init_empty():
    deck = Deck()
    assert len(deck) == 0
    assert deck.cards == []


def test_deck_init_with_cards():
    cards = [_make_card(f"c{i}") for i in range(5)]
    deck = Deck(cards, seed=1)
    assert len(deck) == 5


def test_draw_and_reshuffle():
    cards = [_make_card(f"c{i}") for i in range(3)]
    deck = Deck(cards.copy(), seed=42)
    drawn = [deck.draw() for _ in range(3)]
    assert len(deck) == 0
    deck.add_to_discard(drawn[0])
    deck._reshuffle_discard()
    assert len(deck) == 1


def test_draw_reduces_deck_size():
    cards = [_make_card(f"c{i}") for i in range(5)]
    deck = Deck(cards, seed=1)
    deck.draw()
    assert len(deck) == 4


def test_draw_empty_raises():
    deck = Deck()
    with pytest.raises(IndexError):
        deck.draw()


def test_shuffle_does_not_lose_cards():
    cards = [_make_card(f"c{i}") for i in range(10)]
    deck = Deck(cards, seed=1)
    deck.shuffle()
    assert len(deck) == 10


def test_shuffle_is_deterministic_with_seed():
    cards = [_make_card(f"c{i}") for i in range(10)]
    d1 = Deck(list(cards), seed=42)
    d2 = Deck(list(cards), seed=42)
    d1.shuffle()
    d2.shuffle()
    assert [c.id for c in d1.cards] == [c.id for c in d2.cards]


def test_shuffle_differs_with_different_seeds():
    cards = [_make_card(f"c{i}") for i in range(10)]
    d1 = Deck(list(cards), seed=1)
    d2 = Deck(list(cards), seed=2)
    d1.shuffle()
    d2.shuffle()
    # на 10 картах перестановки с разными сидами почти наверняка отличаются
    assert [c.id for c in d1.cards] != [c.id for c in d2.cards]


def test_add_to_discard():
    deck = Deck()
    c = _make_card("x")
    deck.add_to_discard(c)
    assert c in deck.discard
    assert len(deck) == 0


def test_add_card():
    deck = Deck()
    c = _make_card("x")
    deck.add_card(c)
    assert len(deck) == 1


def test_draw_after_reshuffle_returns_card_from_discard():
    cards = [_make_card(f"c{i}") for i in range(2)]
    deck = Deck(cards, seed=1)
    a = deck.draw()
    b = deck.draw()
    # колода пуста
    assert len(deck) == 0
    deck.add_to_discard(a)
    deck.add_to_discard(b)
    drawn = deck.draw()
    assert drawn in (a, b)


def test_deck_len():
    cards = [_make_card(f"c{i}") for i in range(7)]
    deck = Deck(cards)
    assert len(deck) == 7
