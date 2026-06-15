# Ultimate Fungi Battle 🍄⚔️

> Карточная roguelike-игра в терминале. Грибной воин против сил Тьмы.
> Поле 5×4, 34 карты с эффектами, 6 уровней сложности, декбилдинг-прогрессия.
> Textual TUI с поддержкой мыши, тача и клавиатуры.

![status](https://img.shields.io/badge/status-MVP_completed-brightgreen)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![tests](https://img.shields.io/badge/tests-159_passing-success)
![coverage](https://img.shields.io/badge/coverage-93%25-green)

---

## 🎮 Демо

```
🏔 Лесная опушка  Ход 1  ❤ 20  💰 3  Враг ❤ 20

  ▼Тёмный спорыш   ⚡
   ATK:2/2
   PSN c:2

  [ подготовка ]

  [ подготовка ]

  ▲Алый эльф     ⚡
   ATK:2/3
   GLW c:2
```

---

## 🚀 Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Запустить игру
python src/main.py
```

### Зависимости
- **Python 3.9+**
- **textual** — TUI-фреймворк (для UI)
- **pytest** — для тестов (опционально)

---

## 🎯 Управление

### Клавиатура (ПК, ноутбук, внешняя клавиатура)
| Клавиша | Действие |
|---------|----------|
| `1`–`4` | Выбрать карту в руке (повторное нажатие — поставить) |
| `a`–`e` | Поставить карту в колонку 1-5 |
| `space` | Поставить выбранную карту под курсором |
| `s` | Продать выбранную карту |
| `p` | Пропустить ход |
| `q` | Выход (с сохранением) |
| `↑↓←→` | Курсор по полю |
| `Enter` | Показать инфо о карте |

### Сенсорное управление (Termux, тачскрин)
- **Тап по карте в руке** — выбрать
- **Тап по клетке внизу поля** — поставить туда карту
- **Тап по кнопке** в нижней панели:
  ```
  [1] [2] [3] [4]              выбор карты
  [A] [B] [C] [D] [E]          колонка
  [␣] [$] [✓] [←][↑][↓][→]    действия/курсор
  ```

### Экран Game Over
| Клавиша | Действие |
|---------|----------|
| `R` | Рестарт уровня |
| `N` | Следующий уровень (только при победе) |
| `Q` | Выход |

---

## 🗺️ Уровни

1. **Лесная опушка** — обучение (враги 1/2)
2. **Болото** — медленные, ядовитые
3. **Пещера теней** — высокий урон
4. **Грибная роща** — толпы врагов
5. **Заражённый сад** — эффекты дебаффов
6. **Трон спорового владыки** — финальный босс

Каждый уровень сложнее: больше HP врагов, сильнее эффекты, больше золота нужно.

---

## 🃏 Типы карт и эффектов

**16 эффектов** в игре:
- 💚 **Лечение**: `heal1`, `heal2`, `drain`
- ☠️ **Яды**: `poison`, `deadly_poison`, `spores`
- 🐉 **Сила**: `double_strike`, `spiky`, `growth`
- 🛡️ **Защита**: `fortify`, `taunt`
- 💨 **Утилиты**: `swift`, `glow`, `gold`, `gold3`, `stink`

Карты загружаются из `src/assets/cards.json`.

---

## 🧪 Тестирование

```bash
# запустить все тесты
PYTHONPATH=src python -m pytest src/tests/

# с покрытием
PYTHONPATH=src python -m pytest src/tests/ --cov=src/game --cov-report=term

# конкретный файл
PYTHONPATH=src python -m pytest src/tests/test_engine.py -v
```

**Текущее состояние:** 159 тестов, **93% покрытие** ядра игры.

| Файл | Тестов | Что проверяет |
|------|--------|---------------|
| `test_ai.py` | 9 | AI-логика |
| `test_card.py` | 5 | Структура карты |
| `test_card_loader.py` | 9 | Загрузка JSON |
| `test_deck.py` | 12 | Операции с колодой |
| `test_effects.py` | 22 | Все 16 эффектов |
| `test_engine.py` | 39 | Игровой цикл |
| `test_levels.py` | 7 | Уровни |
| `test_levels_progression.py` | 5 | Прогрессия |
| `test_state.py` | 8 | Модели данных |
| `test_ui_render.py` | 22 | Рендер виджетов |
| `test_touch.py` | 21 | Сенсорное управление |

---

## 📁 Структура проекта

```
src/
├── main.py                 # точка входа
├── game/                    # ядро игры (без зависимостей от UI)
│   ├── engine.py            # GameEngine — главный цикл
│   ├── state.py             # Cell, Board, PlayerState, GameState
│   ├── card.py              # Card dataclass
│   ├── deck.py              # Deck — добор, перемешивание, продажа
│   ├── card_loader.py       # загрузка карт из JSON
│   ├── effects.py           # 16 эффектов + EFFECT_REGISTRY
│   ├── ai.py                # AI-логика
│   ├── levels.py            # 6 уровней + GameEngine.create_for_level
│   └── save.py              # сохранение/загрузка (заглушка)
├── ui/                      # Textual TUI
│   ├── textual_app.py       # FungiBattleApp, GameOverScreen, BoardCell, HandCard
│   └── animations.py        # анимации (заглушки time.sleep)
├── assets/
│   ├── cards.json           # 34 карты с эффектами
│   └── levels/              # конфиги уровней
└── tests/                   # 159 тестов

plan.md                      # подробный план + roadmap
```

---

## 🛠️ Разработка

### План
Полный план в [`plan.md`](plan.md) — архитектура, реализованные
фичи, TODO, roadmap, баги и решения.

### Архитектура
- **MVC**: game/ (модель) ↔ ui/ (вид) ↔ main.py (контроллер)
- **Reactive UI**: `BoardCell`, `HandCard` — реактивные виджеты
- **Эффекты как плагины**: `@register(effect_id)` декоратор

### Добавить новую карту
1. Открой `src/assets/cards.json`
2. Добавь объект:
   ```json
   {
     "id": "my_mushroom",
     "name": "Микоризный страж",
     "cost": 4,
     "atk": 3,
     "hp": 5,
     "max_hp": 5,
     "effect_id": "taunt"
   }
   ```
3. Запусти игру — карта в колоде

### Добавить новый эффект
1. Открой `src/game/effects.py`
2. Добавь функцию:
   ```python
   @register("my_effect")
   def my_effect(card, state, owner):
       # ... логика ...
       return "Сообщение"
   ```
3. Используй `"effect_id": "my_effect"` в карте

---

## 🐛 Известные ограничения

- ⏳ Сохранение/загрузка — пока заглушка
- ⏳ Анимации — `time.sleep` placeholders
- ⏳ Только один AI (лёгкий); средний/сложный — в плане

---

## 📜 Лицензия

MIT — делай что хочешь.

## 🍄 Благодарности

- [Textual](https://github.com/Textualize/textual) — за крутой TUI-фреймворк
- Вдохновлено *Slay the Spire*, *Inscryption*, *Mushroom Wars*
