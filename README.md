# Familiada App

An application simulating the *Family Feud* game show, controlled from a terminal-style command bar and rendered as graphics in a **Pygame** window. The project recreates the full flow of the game - from the home screen, through the elimination rounds, to the final round and the win/lose end screen.

## Table of contents

- [How it works](#how-it-works)
- [Project architecture](#project-architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the app](#running-the-app)
- [Data structure](#data-structure)
- [Controls and commands](#controls-and-commands)
- [Game flow](#game-flow)
- [Sounds](#sounds)
- [Repository structure](#repository-structure)

## How it works

The game is driven by a host (operator) who types commands into the terminal-style input bar at the bottom of the screen. Depending on the current stage of the game (`stage`), the same commands (e.g. an answer number or `x`) trigger different actions (this logic is handled by a state machine inside `Engine`).

The game consists of two main stages:

1. **Elimination round** (6 questions, each with a different number of possible answers) - teams guess answers from the answer board, collecting points; three mistakes hand the pot over to the other team for a chance to "steal" it. After the last question, the game moves directly into the final round.
2. **Final round** - a player from each team answers 6 questions against the clock (15s for player 1, 20s for player 2), either by selecting the number of a ready-made answer or typing free text; answers are revealed one by one, and at the end a win or lose screen is shown depending on the total points scored.

## Project architecture

The code is split by single responsibility into the following components:

| File | Responsibility |
|---|---|
| `main.py` | Entry point — initializes the components and runs the main game loop |
| `game_state.py` | `GameState` class — stores and validates the entire game state (points, stage, answers, mistakes) |
| `engine.py` | `Engine` class — the state machine that drives the game based on commands and the current stage; also handles the final-round timer and triggers sound effects |
| `loader.py` | `Loader` class — loads and caches images (answers, boards, characters, mistake icons) and sounds from the `data/` folder |
| `renderer.py` | `Renderer` class — draws the game board on a PIL canvas, displays it in the Pygame window, and plays sounds via `pygame.mixer` |
| `gui.py` | `GUI` class — handles keyboard events, the command buffer (including arbitrary free text for custom final-round answers), and the text terminal at the bottom of the screen |

Data flow is one-directional: `GUI` collects a command from the operator → `Engine` interprets it in the context of `GameState` → `Engine` asks `Renderer` to draw the changes and play a sound, using assets loaded by `Loader`.

## Requirements

- Python 3.10+ (the code uses `int | None` syntax)
- Dependencies from `requirements.txt`:
  - `pygame==2.6.1`
  - `pillow==12.0.0`

## Installation

```bash
git clone https://github.com/jksikora/familiada_app.git
cd familiada_app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the app

```bash
python main.py
```

The game opens in fullscreen mode (`pygame.FULLSCREEN`). Commands are typed into the terminal field at the bottom of the screen and submitted with **Enter**.

## Data structure

All graphic and audio assets live in the `data/` folder:

```
data/
├── answers/           # Answer graphics
│   ├── elimination/   # q1–q6, files named aN_<points>.png
│   └── final/         # q1–q6/turn1, turn2
├── assets/            # Backgrounds, boards, static elements (elimination, final/turn1, turn2)
│                      # including home_screen.png, ending_win.png, ending_lose.png
├── chars/             # Individual character glyphs (letters, digits, special characters) used to render text on the board
├── mistakes/          # "X" mistake graphics, small and large, per team
└── sounds/            # Sound effects played via pygame.mixer (see the "Sounds" section)
```

`Loader` builds file paths dynamically based on the game stage, question number and turn (e.g. `data/answers/elimination/q1/a3_25.png`, where `25` is the point value read directly from the filename).

## Controls and commands

| Command | Meaning |
|---|---|
| *(empty, Enter)* | Confirm / move forward |
| `1`, `2` | Select team / player number |
| `1`–`9`, `0` | Select an answer number or enter a value |
| `x` | Mark a wrong answer |
| `next` | Move to the next question/stage |
| `start` | Start the countdown in the final round, or reset the game from the end screen |
| `s` | Skip a question in the final round |
| `>` | Reveal the next answer (reveal phase) |
| *(any free text)* | In the final round: a player's own custom answer |

The availability of each command depends on the current game stage (`GameState.current_stage`) and is validated by `Engine`. 

## Game flow

1. **Home screen** (`home`): pressing Enter moves to the start confirmation.
2. **Elimination round** (`elimination_start` → `elimination` → `elimination_reveal`): repeated 6 times, with the number of possible answers varying per question (5, 4, 5, 5, 6, 5), as defined in `ELIMINATION_ROUNDS_CONFIG`. Three mistakes (`x`) trigger the steal phase for the other team. Once the last question is finished, the game automatically moves straight into the final round.
3. **Final round** (`final` → `final_reveal`): player 1 gets 15 seconds, player 2 gets 20 seconds to give 6 answers (either numeric, picked from the answer list, or free text). Player 2's answers are automatically checked for duplicates against player 1's answers (signaled with the `repeated` sound).
4. **End of game** (`end` → `end_confirm`): once all answers are revealed, a win screen (`ending_win`) or lose screen (`ending_lose`) is shown, depending on whether the total score reached the 200-point threshold. The operator can confirm quitting (`enter` → `enter`) or reset the game back to the home screen (`start`).

## Sounds

Sound effects (`data/sounds/`) are played through `Renderer.play_sound()` at key moments in the game:

| File | When it's played |
|---|---|
| `elimination_round_starts.wav` | Start of each elimination round |
| `correct.wav` | A correctly revealed answer |
| `wrong.wav` | A wrong answer (`x`) or a failed steal attempt |
| `final_starts.wav` | Start of the final round |
| `repeated.wav` | Player 2 gives an answer that duplicates player 1's |
| `final_round_ends.wav` | End of player 1's turn in the final round (handing off to player 2) |
| `familiada_theme.wav` | End of the whole game (end screen) |

`Loader.load_sound()` supports both `.wav` and `.mp3` files; a missing sound file doesn't crash the game, the error is simply logged to the console.

## Repository structure

```
familiada_app/
├── data/              # Graphic and audio assets (see "Data structure")
├── engine.py          # Game logic and state machine
├── game_state.py      # Game state model
├── gui.py             # Input handling and terminal bar
├── loader.py          # Loading assets from disk
├── main.py            # Application entry point
├── renderer.py        # Board rendering and sound playback
└── requirements.txt   # Python dependencies
```
