from typing import List, Optional
from .state import GameState


class AI:
    def __init__(self, difficulty: str = "easy"):
        self.difficulty = difficulty

    def take_turn(self, state: GameState) -> Optional[List[tuple]]:
        """Вернуть список (card_id, column) — карты, которые нужно сыграть.

        Упрощённый AI: каждую доступную карту ставит в первую свободную колонку
        (сверху вниз по колонкам). Золото не списываем здесь — это делает
        play_card_by_id.
        """
        p = state.enemy
        moves = []
        used_cols = set()
        for idx, card in enumerate(list(p.hand)):
            if card.cost > p.gold:
                continue
            # ищем первую свободную колонку, ещё не использованную в этом ходу
            for c in range(state.board.width):
                if c in used_cols:
                    continue
                row = 0
                cell = state.board.cell(row, c)
                if cell.card is None:
                    moves.append((card.id, c))
                    used_cols.add(c)
                    break
        return moves
