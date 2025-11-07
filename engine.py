from PIL import Image
from loader import Loader, PANEL_WIDTH, PANEL_HEIGHT

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1040

ELIMINATION_POSITIONS = {
    "team1_points_position": (3,3),
    "team2_points_position": (3,32),
    "team1_small_x_position": (5,1),
    "team1_big_x_position": (7,1),
    "team2_small_x_position": (5,30),
    "team2_big_x_position": (7,30),
    "answers_num_position": (5,5),
    "answers_position": (5,7),
    "answers_points_position": (5,27),
    "elimination_sum_position": (12,28)
}

FINAL_POSITIONS = {
    "player1_answer_position": (4,2),
    "player1_points_position": (4,14),
    "player2_answer_position": (4,21),
    "player2_points_position": (4,18),
    "final_sum_position": (11,20)
}

POSITIONS = {
    "elimination": ELIMINATION_POSITIONS,
    "final": FINAL_POSITIONS
}

# --- Main logic ---
class Engine:
    def __init__(self):
        self.loader = Loader() 

        self.team1_points = 0
        self.team2_points = 0
        self.team1_mistakes = 0
        self.team2_mistakes = 0

        self.current_stage = "elimination" #or "final"
        self.current_turn = 1 #or 2
        self.current_question_num = 1 #max 6
        self.current_answer_num = 1 #max 6
        self.num_answers = 5 #max 6
        
        self.canvas = self.create_opening_screen()

    # --- Helper ---
    def _panels_to_pixels(self, panel_x: int, panel_y: int):
        x = (panel_x - 1) * PANEL_WIDTH
        y = (panel_y - 1) * PANEL_HEIGHT
        return x, y

    def paste_image(self, img: Image.Image, row: int, col: int):
        if img is None:
            raise ValueError("[Engine]: Image is None")
        x = col * PANEL_WIDTH
        y = row * PANEL_HEIGHT
        self.canvas.paste(img, (x,y), img)

    def paste_number(self, number: int, row: int, col: int, digits: int | None = None):
        if digits is not None:
            num_str = str(number).zfill(digits)
        else:
            num_str = str(number)
        
        for i, num in enumerate(num_str):
            img = self.loader.get_char(num)
            if img:
                self.paste_image(img, row, col + i)
    
    # --- App Home Screen ---
    def create_opening_screen(self) -> Image.Image:
        try:
            opening_screen = self.loader.load_asset("opening")
            if opening_screen is not None:
                return opening_screen.copy()
        except Exception as e:
            raise ValueError(f"[Engine]: Failed to load opening screen: {e}")

    # --- Game Initialization ---
    def create_layout(self, stage: str, num_answers: int | None = None, turn: int | None = None):
        self.current_stage = stage
        self.num_answers = num_answers

        try:
            screen = self.loader.load_asset("screen")
            if screen is not None:
                self.canvas = screen.copy()
        except Exception as e:
            raise ValueError(f"[Engine]: Failed to load screen: {e}")
        
        if stage == "elimination":
            map = POSITIONS[stage]
            x_team1_points_start, y_team1_points_start = map["team1_points_position"] 
            x_team2_points_start, y_team2_points_start = map["team2_points_position"] 
            x_answers_num_start, y_answers_num_start = map["answers_num_position"]
            x_sum_start, y_sum_start = map[f"{stage}_sum_position"]

            for i in range(1, num_answers + 1):
                num_img = self.loader.get_char(str(i))
                if num_img:
                    self.paste_image(num_img, x_answers_num_start + (i - 1), y_answers_num_start)

            try:
                layout = self.loader.load_layout(stage, turn, num_answers)
                if layout: 
                    for i in range(1, num_answers + 1):
                        img = layout.get(i)
                        if img:
                            self.paste_image(img, 0, 0)
            except Exception as e:
                raise ValueError(f"[Engine]: Failed to load layout: {e}")
            
            self.paste_number(0, x_team1_points_start, y_team1_points_start, digits = 3)
            self.paste_number(0, x_team2_points_start, y_team2_points_start, digits = 3)

            sum_img = layout.get("sum")
            if sum_img:
                self.paste_image(sum_img, 0, 0)
                self.paste_number(0, x_sum_start, y_sum_start, digits = 3)
            
        elif stage == "final":
            map = POSITIONS[stage]
            x_sum_start, y_sum_start = map[f"{stage}_sum_position"]

            try:
                layout = self.loader.load_layout(stage, turn, num_answers)
                if layout: 
                    for i in range(1, num_answers + 1):
                        img = layout.get(i)
                        if img:
                            self.paste_image(img, 0, 0)
            except Exception as e:
                raise ValueError(f"[Engine]: Failed to load layout: {e}")
        
            sum_img = layout.get("sum")
            if sum_img:
                self.paste_image(sum_img, 0, 0)
                self.paste_number(0, x_sum_start, y_sum_start, digits = 3)
