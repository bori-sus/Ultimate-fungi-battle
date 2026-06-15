"""Тесты для Card."""
from game.card import Card


def test_card_creation_minimal():
    c = Card(id="x", name="X", cost=1, atk=2, hp=3, max_hp=3)
    assert c.id == "x"
    assert c.name == "X"
    assert c.cost == 1
    assert c.atk == 2
    assert c.hp == 3
    assert c.max_hp == 3


def test_card_defaults():
    c = Card(id="x", name="X", cost=1, atk=1, hp=1, max_hp=1)
    assert c.description == ""
    assert c.ascii_top == ""
    assert c.ascii_bottom == ""
    assert c.tags is None
    assert c.persistent is False
    assert c.effect_id is None


def test_card_to_dict():
    c = Card(id="x", name="X", cost=2, atk=3, hp=4, max_hp=4,
             description="d", effect_id="glow")
    d = c.to_dict()
    assert d["id"] == "x"
    assert d["name"] == "X"
    assert d["cost"] == 2
    assert d["atk"] == 3
    assert d["hp"] == 4
    assert d["max_hp"] == 4
    assert d["description"] == "d"
    assert d["effect_id"] == "glow"


def test_card_from_dict():
    data = {
        "id": "y", "name": "Y", "cost": 1, "atk": 1, "hp": 1, "max_hp": 1,
        "description": "test", "effect_id": None
    }
    c = Card.from_dict(data)
    assert c.id == "y"
    assert c.name == "Y"
    assert c.description == "test"


def test_card_roundtrip():
    c = Card(id="z", name="Z", cost=3, atk=2, hp=5, max_hp=5, effect_id="heal1")
    data = c.to_dict()
    c2 = Card.from_dict(data)
    assert c2.id == c.id
    assert c2.cost == c.cost
    assert c2.effect_id == c.effect_id
