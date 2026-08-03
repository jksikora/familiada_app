from PIL import Image
import pygame
from loader import Loader

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1040
TERMINAL_HEIGHT = 40

ELIMINATION_POSITIONS = {
    "team1_points_position": (2,0),
    "team2_points_position": (2,29),
    "team1_mistakes_position": (4,0),
    "team2_mistakes_position": (4,29),
    "answers_num_position": (4,4),
    "answers_position": (4,6),
    "answers_points_position": (4,26),
    "elimination_sum_position": (11,25)
}

FINAL_POSITIONS = {
    "player1_answer_position": (3,1),
    "player1_points_position": (3,13),
    "player2_answer_position": (3,20),
    "player2_points_position": (3,17),
    "final_sum_position": (10,17),
    "final_timer_position": (1,15)
}

END_POSITIONS = {
    "end_sum_position": (7, 17)
}

POSITIONS = {
    "elimination": ELIMINATION_POSITIONS,
    "final": FINAL_POSITIONS,
    "end": END_POSITIONS
}

class Renderer:
    def __init__(self, loader: Loader):
        # --- Initialize PIL base --- 
        self.loader = loader
        self.width = CANVAS_WIDTH
        self.height = CANVAS_HEIGHT
        self.positions = POSITIONS

        self.canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        # --- Initialize Pygame Display ---
        pygame.init()
        pygame.mixer.init()
        self.terminal_height = TERMINAL_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height + self.terminal_height), pygame.FULLSCREEN)
        self.font = pygame.font.Font(None, 15)
        self.terminal_background_color = (15, 15, 15)
        self.terminal_text_color = (220, 220, 220)
        self.terminal_log_color = (180, 180, 180)

        self.terminal_text = ""


    # === Helpers ===
    def clear_canvas(self) -> None:
        self.canvas = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

    def _clear_area(self, row: int, col: int, num_panels: int = 1) -> None:
        panel = self.loader.load_asset("panel")
        for i in range(num_panels):
            self._paste_image(panel, row, col + i)
    
    def _clear_answer_area(self, stage: str, question_num: int, answer_num: int | None = None, turn: int | None = None) -> None:
        if stage == "elimination":
            answer_pos = self.positions[stage]["answers_position"]
            self._clear_area(answer_pos[0] + answer_num - 1, answer_pos[1], 22)
        elif stage == "final":
            if turn == 1:
                # Player 1: points are to the right of answers
                answer_pos = self.positions[stage]["player1_answer_position"]
                self._clear_area(answer_pos[0] + question_num - 1, answer_pos[1], 14)
            else:
                # Player 2: points are to the LEFT of answers, so clear from points position
                points_pos = self.positions[stage]["player2_points_position"]
                # Clear 14 panels wide (3 for points + 11 for answer area)
                self._clear_area(points_pos[0] + question_num - 1, points_pos[1], 14)
    
    def _clear_mistakes_area(self) -> None:
        for i in range(1, 10):
            team1_mistake_pos = self.positions["elimination"]["team1_mistakes_position"]
            team2_mistake_pos = self.positions["elimination"]["team2_mistakes_position"]
            self._clear_area(team1_mistake_pos[0] + i, team1_mistake_pos[1], 3)
            self._clear_area(team2_mistake_pos[0] + i, team2_mistake_pos[1], 3)

    def _paste_image(self, img: Image.Image, row: int, col: int) -> None:
        self._validate_int("row", row, range(0, (self.height // 80)+1))
        self._validate_int("col", col, range(0, (self.width // 60)+1))
        x, y = col * 60, row * 80
        self.canvas.paste(img, (x, y), img)

    def _draw_number(self, number: int, row: int, col: int, digits: int = 3) -> None:
        num_str = str(number).zfill(digits)
        for i, num in enumerate(num_str):
            img = self.loader.get_char(num)
            self._paste_image(img, row, col + i)
    
    def _draw_layout_base(self, layout: dict, num_answers: int | None = None) -> None:
        for key, img in layout.items():
            if isinstance(key, int) or key =="sum":
                self._paste_image(img, 0, 0)

        if "numbers" in layout and num_answers:
            answers_num_pos = self.positions["elimination"]["answers_num_position"]
            for i, num_img in enumerate(layout["numbers"], start=0):
                self._paste_image(num_img, answers_num_pos[0] + i, answers_num_pos[1])

    def _pil_to_pygame(self, img: Image.Image):
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def _validate_int(self, name: str, value: int, valid_range: range | None = None, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[Renderer]: Invalid {name} input - {name} cannot be None")
            return

        if not isinstance(value, int): # Type check
            raise TypeError(f"[Renderer]: Expected int {name}, got: {type(value)}")
        if valid_range is not None and value not in valid_range: # Value check
            raise ValueError(f"[Renderer]: Invalid {name} input - '{name}' must be in range {list(valid_range)}, is: {value}")
    
    def _validate_str(self, name: str, value: str, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[Renderer]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, str): # Type check
            raise TypeError(f"[Renderer]: Expected str {name}, got: {type(value)}")
        
        if not value.strip() and not allow_none:
            raise ValueError(f"[Renderer]: Invalid {name} input - {name} cannot be empty")

    # === Home & End Screens ===
    def draw_home_screen(self) -> None:
        self.clear_canvas()
        home_screen = self.loader.load_asset("home_screen")
        self._paste_image(home_screen, 0, 0)
    
    def draw_end_screen(self, sum: int) -> None:
        self.clear_canvas()
        
        # Choose ending asset based on sum threshold
        if sum >= 200:
            end_screen = self.loader.load_asset("ending_win")
        else:
            end_screen = self.loader.load_asset("ending_lose")
        
        self._paste_image(end_screen, 0, 0)

        sum_pos = self.positions["end"]["end_sum_position"]
        self._draw_number(sum, sum_pos[0], sum_pos[1])


    # === Elimination Stage ===
    def draw_elimination_layout(self, num_answers: int, team_points: dict, sum: int) -> None:
        self.clear_canvas()

        screen = self.loader.load_asset("screen")
        self._paste_image(screen, 0, 0)

        layout = self.loader.load_layout("elimination", num_answers, None)
        self._draw_layout_base(layout, num_answers)

        self._clear_mistakes_area()

        # vignette = self.loader.load_asset("vignette")
        # self._paste_image(vignette, 0, 0)
        
        self.draw_team_points(team_points)
        self.draw_sum(sum, "elimination")
    

    # === Final Stage ===
    def draw_final_layout(self, turn: int, sum: int) -> None:
        self.clear_canvas()

        screen = self.loader.load_asset("screen")
        self._paste_image(screen, 0, 0)

        self._clear_mistakes_area()

        # Draw both players' halves so the full final board is visible
        turn1_layout = self.loader.load_layout("final", 6, turn=1)
        turn2_layout = self.loader.load_layout("final", 6, turn=2)
        self._draw_layout_base(turn1_layout)
        self._draw_layout_base(turn2_layout)

        # vignette = self.loader.load_asset("vignette")
        # self._paste_image(vignette, 0, 0)

        self.draw_sum(sum, "final")
    

    # === Utilities ===
    def draw_answer(self, stage: str, question_num: int, answer_num: int, turn: int | None = None) -> int:
        img, path = self.loader.get_answer(stage, question_num, answer_num, turn)

        self._clear_answer_area(stage, question_num, answer_num if stage=="elimination" else None, turn if stage=="final" else None)

        self._paste_image(img, 0, 0)
        points = self.loader.get_points(path)
        return points

    def draw_mistake(self, big: bool, turn: int, mistake_num: int | None = None) -> None:
        x_img = self.loader.get_x(big, turn, mistake_num)
        self._paste_image(x_img, 0, 0)
    
    def draw_team_points(self, team_points: dict) -> None:
        team1_pos = self.positions["elimination"]["team1_points_position"]
        team2_pos = self.positions["elimination"]["team2_points_position"]
        self._clear_area(team1_pos[0], team1_pos[1], 3)
        self._clear_area(team2_pos[0], team2_pos[1], 3)
        self._draw_number(team_points.get(1, 0), team1_pos[0], team1_pos[1])
        self._draw_number(team_points.get(2, 0), team2_pos[0], team2_pos[1])

    def draw_sum(self, sum: int, stage: str) -> None:
        if stage == "elimination":
            sum_pos = self.positions["elimination"]["elimination_sum_position"]
        elif stage == "elimination_reveal":
            sum_pos = self.positions["elimination"]["elimination_sum_position"]
        elif stage == "final":
            sum_pos = self.positions["final"]["final_sum_position"]
        elif stage == "final_reveal":
            sum_pos = self.positions["final"]["final_sum_position"]
        else:
            sum_pos = self.positions["end"]["end_sum_position"]
        self._clear_area(sum_pos[0], sum_pos[1], 3)
        self._draw_number(sum, sum_pos[0], sum_pos[1])
    
    def draw_custom_answer(self, stage: str, turn: int, question_num: int, answer: str, points: int) -> None:
        self._validate_str("stage", stage)
        self._validate_int("turn", turn, range(1,3))
        self._validate_int("question_num", question_num, range(1,7))
        self._validate_str("answer", answer)
        self._validate_int("points", points)

        # Base position for the player's answer area
        if turn == 1:
            row, col = self.positions["final"]["player1_answer_position"]
        else:
            # Player 2: start from points position and clear both points + answer
            row, col = self.positions["final"]["player2_points_position"]
        
        # Each question is one row below the previous one
        x = row + (question_num - 1)
        y = col

        if stage != "final":
            raise NotImplementedError(f"[Renderer]: Custom answers only supported in 'final' stage, got: {stage}")

        # Clear the exact row where we'll draw the custom answer
        self._clear_area(x, y, 14)

        # Draw each character of the custom answer at the correct slot
        # For player 2, offset the drawing to start at answer position (3 cols to the right)
        answer_offset = 3 if turn == 2 else 0
        for i, char in enumerate(answer):
            if char == " ":
                img = self.loader.get_space()
            else:
                img = self.loader.get_char(char)
            self._paste_image(img, x, y + answer_offset + i)

        # Draw points for this custom answer in the points column
        points_pos = (
            self.positions["final"]["player1_points_position"]
            if turn == 1
            else self.positions["final"]["player2_points_position"]
        )
        points_row = points_pos[0] + (question_num - 1)
        points_col = points_pos[1]
        # Clear points area (3 panels) and draw the number
        self._clear_area(points_row, points_col, 3)
        self._draw_number(points, points_row, points_col, 2)


    def draw_timer(self, time_left: int) -> None: 
        self._validate_int("time_left", time_left, range(0,21))
        
        timer_pos = self.positions["final"]["final_timer_position"]
        self._draw_number(time_left, timer_pos[0], timer_pos[1], 2)

    def clear_timer(self) -> None:
        timer_pos = self.positions["final"]["final_timer_position"]
        self._clear_area(timer_pos[0], timer_pos[1], 2)


    # === Sound ===
    def play_sound(self, sound_name: str) -> None:
        # --- Plays a sound by name (correct, wrong, repeated) ---
        self._validate_str("sound_name", sound_name)
        try:
            sound = self.loader.load_sound(sound_name)
            sound.play()
        except Exception as e:
            print(f"[Renderer]: Could not play sound '{sound_name}': {e}")


    # === Terminal Bar ===
    def draw_terminal(self, input_buffer: str, latest_log: str = "") -> None:
        self._validate_str("input_buffer", input_buffer)
        self._validate_str("latest_log", latest_log, allow_none=True)

        # Draw terminal background
        terminal = pygame.Rect(0, self.height, self.width, self.terminal_height)
        pygame.draw.rect(self.screen, self.terminal_background_color, terminal)

        # Draw latest log above input
        if latest_log:
            log_surface = self.font.render(latest_log, True, self.terminal_log_color)
            self.screen.blit(log_surface, (20, self.height + 4))

        # Draw input line
        input_surface = self.font.render(input_buffer, True, self.terminal_text_color)
        self.screen.blit(input_surface, (20, self.height + 21))

    # === Display Management ===
    def render(self) -> None:
        surface = self._pil_to_pygame(self.canvas)
        self.screen.blit(surface, (0, 0))
        pygame.display.flip()
    
    def get_canvas(self) -> Image.Image:
        return self.canvas
