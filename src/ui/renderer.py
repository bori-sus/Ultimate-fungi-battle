try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False


if RICH_AVAILABLE:
    console = Console()


    def render_board(board):
        table = Table.grid()
        for r in range(board.height):
            row_cells = []
            for c in range(board.width):
                cell = board.cell(r, c)
                if cell.card:
                    row_cells.append(f"[{cell.owner[0].upper()}]{cell.card.name}({cell.card.atk}/{cell.card.hp})")
                else:
                    row_cells.append("[     ]")
            table.add_row(*row_cells)
        console.print(table)


    def render_hand(hand):
        console.print("Рука:")
        for idx, card in enumerate(hand, start=1):
            console.print(f"{idx}. {card.name} (cost:{card.cost} atk:{card.atk} hp:{card.hp})")


    def render_state(state):
        console.rule(f"Turn {state.turn_number} — Игрок HP:{state.player.hp} Gold:{state.player.gold} | Враг HP:{state.enemy.hp} Gold:{state.enemy.gold}")
        render_board(state.board)
        render_hand(state.player.hand)
else:

    def render_board(board):
        print("Board:")
        for r in range(board.height):
            row_cells = []
            for c in range(board.width):
                cell = board.cell(r, c)
                if cell.card:
                    row_cells.append(f"{cell.owner[0].upper()}:{cell.card.name}({cell.card.atk}/{cell.card.hp})")
                else:
                    row_cells.append("[     ]")
            print(" | ".join(row_cells))


    def render_hand(hand):
        print("Рука:")
        for idx, card in enumerate(hand, start=1):
            print(f"{idx}. {card.name} (cost:{card.cost} atk:{card.atk} hp:{card.hp})")


    def render_state(state):
        print(f"Turn {state.turn_number} — Игрок HP:{state.player.hp} Gold:{state.player.gold} | Враг HP:{state.enemy.hp} Gold:{state.enemy.gold}")
        render_board(state.board)
        render_hand(state.player.hand)
