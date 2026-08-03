from loader import Loader
from game_state import GameState
from renderer import Renderer
from gui import GUI
from engine import Engine

# Initialize components
loader = Loader()
gamestate = GameState()
renderer = Renderer(loader)
gui = GUI(renderer)
engine = Engine(loader, gamestate, renderer, gui)

# Draw home screen at start
renderer.draw_home_screen()
gui.set_message("Welcome to the Game! Press 'Enter' to start.")

while gui.is_running():
    gui.update()
    command = gui.get_command()

    # Pass command and timer update to engine
    engine.update_final_timer()
    if command is not None:
        engine.handle_command(command)