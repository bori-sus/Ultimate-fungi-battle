import json
from typing import Any


def save_game(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
