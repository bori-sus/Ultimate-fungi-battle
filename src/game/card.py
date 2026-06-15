from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class Card:
    id: str
    name: str
    cost: int
    atk: int
    hp: int
    max_hp: int
    description: str = ""
    ascii_top: str = ""
    ascii_bottom: str = ""
    tags: Optional[list] = None
    persistent: bool = False
    effect_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Card":
        return Card(**data)
