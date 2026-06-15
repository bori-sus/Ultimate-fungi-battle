"""Простейший обработчик ввода: поддерживает команды из engine.run()
"""


def get_input(prompt: str = "> ") -> str:
    try:
        return input(prompt)
    except EOFError:
        return "q"
