from PIL import Image 
import os, glob

DATA_FOLDER = "data"
PANEL_WIDTH = 60
PANEL_HEIGHT = 80

SPECIAL_CHARACTERS = {
    ".": "DOT.png",
    "(": "LPAREN.png",
    ")": "RPAREN.png",
    "-": "DASH.png",
    "*": "NULL.png",
    "_": "UNDERSCORE.png",
    "#": "HASH.png",
}

class Loader:
    def __init__(self) -> None:
        self.data_foler = DATA_FOLDER
        self.assets_path = os.path.join(self.data_foler, "assets")
        self.answers_path = os.path.join(self.data_foler, "answers")
        self.mistakes_path = os.path.join(self.data_foler, "mistakes")
        self.chars_path = os.path.join(self.data_foler, "chars")
        self.cache = {}

    # --- Helper ---
    def _load_image(self, path: str) -> Image.Image | None:
        if path in self.cache:
            return self.cache[path]
        
        if not os.path.exists(path):
            raise ValueError(f"[Loader]: Missing image: {path}")
        
        img = Image.open(path)
        self.cache[path] = img
        return img
    
    # ---Answers ---
    def get_answer(self, stage: str, question_num: str, answer_num: int, turn: int | None = None) -> Image.Image | None:
        if stage == "final":
            if turn is None:
                raise ValueError(f"[Loader]: Final stage requires turn")
            folder_path = os.path.join(self.answers_path, stage, f"q{question_num}", f"turn{turn}") 
        else:
            folder_path = os.path.join(self.answers_path, stage, f"q{question_num}")

        pattern = os.path.join(folder_path, f"a{answer_num}_*.png")
        files = glob.glob(pattern)

        if not files:
            raise ValueError(f"[Loader]: No files found for pattern: {pattern}")
        
        path = files[0]
        return self._load_image(path) 
        
    # --- Chars ---
    def get_char(self, char: str) -> Image.Image | None:
        path = os.path.join(self.chars_path, f"{char.upper()}.png")
        return self._load_image(path)
    
    def create_space(self) -> Image.Image:
        return Image.new("RGBA", (PANEL_WIDTH, PANEL_HEIGHT), (0, 0, 0, 0))
    
    # --- Mistakes ---
    def get_x(self, big: bool = False) -> Image.Image | None:
        filename = "x_big.png" if big else "x_small.png"
        path = os.path.join(self.mistakes_path, filename)
        return self._load_image(path)
    
    # --- Assets ---
    def load_asset(self, filename: str) -> Image.Image | None:
        path = os.path.join(self.assets_path, f"{filename}.png")
        return self._load_image(path)
    
    def load_sum(self, stage: str) -> Image.Image:
        path = os.path.join(self.assets_path, stage, "sum.png")
        return self._load_image(path) 
    
    def load_layout(self, stage: str, turn: int | None = None, num_answers: int | None = 6) -> dict[int, Image.Image]:
        layout = {}

        if stage == "final":
            if turn is None:
                raise ValueError(f"[Loader]: Final stage requires turn")
            stage_path = os.path.join(self.assets_path, stage, f"turn{turn}")
        elif stage == "elimination":
            stage_path = os.path.join(self.assets_path, stage)
        else:
            raise ValueError(f"[Loader]: Invalid stage name: {stage}")
        
        for i in range(1, num_answers + 1):
            path = os.path.join(stage_path, f"a{i}.png")
            img = self._load_image(path)
            if img:
                layout[i] = img

        sum_path = os.path.join(self.assets_path, stage, "sum.png")
        sum_img = self._load_image(sum_path)
        if sum_img:
            layout["sum"] = sum_img

        return layout