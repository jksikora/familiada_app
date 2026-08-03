import pygame
from renderer import Renderer

COMMANDS = {
    "": "enter",
    "x": "x",
    "next": "next",
    "start": "start",
    "s": "s",
    ">": ">",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "0": "0",
}

class GUI:
    def __init__(self, renderer: Renderer):
        # --- References ---
        self.renderer = renderer
        self.commands = COMMANDS

        # --- Input State ---
        self.input_buffer = ""
        self.logs: list[str] = []

        # --- Command buffer ---
        self.submit_command = None

        # --- Internal Control ---
        self.running = True
    
    def _validate_str(self, name: str, value: str, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, str): # Type check
            raise TypeError(f"[Loader]: Expected str {name}, got: {type(value)}")
        
        if not value.strip():
            raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be empty")

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                normalized_command = self.input_buffer.lower()
                # Submit mapped command if in COMMANDS dict, otherwise pass raw input
                if normalized_command in self.commands:
                    self.submit_command = self.commands[normalized_command]
                else:
                    # Allow any non-empty input (for custom text answers in final stage)
                    self.submit_command = normalized_command if normalized_command.strip() else None
                
                if self.submit_command is not None:
                    self.logs.append(normalized_command)
                    self.input_buffer = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            else:
                char = event.unicode
                if char.isprintable():
                    self.input_buffer += char
    
    def get_command(self) -> str | None:
        if self.submit_command is not None:
            command = self.submit_command
            self.submit_command = None
            return command
        return None
    
    def set_message(self, text: str) -> None:
        self._validate_str("text", text)
        self.logs.append(text)
    
    def update(self) -> None:
        for event in pygame.event.get():
            self.handle_event(event)

        latest_log = self.logs[-1] if self.logs else None
        input_buffer = f"> {self.input_buffer}" 
        self.renderer.draw_terminal(input_buffer, latest_log)

        self.renderer.render()

    def is_running(self) -> bool:
        return self.running