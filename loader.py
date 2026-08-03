from PIL import Image 
import os, glob, re
import pygame

# === Global Constants ===
DATA_FOLDER = "data"
PANEL_WIDTH = 60
PANEL_HEIGHT = 80

# === Special Characters Map ===
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
        # Base data paths
        self.data_folder = DATA_FOLDER
        self.assets_path = os.path.join(self.data_folder, "assets")
        self.answers_path = os.path.join(self.data_folder, "answers")
        self.mistakes_path = os.path.join(self.data_folder, "mistakes")
        self.chars_path = os.path.join(self.data_folder, "chars")
        self.sounds_path = os.path.join(self.data_folder, "sounds")

        self.panel_width = PANEL_WIDTH
        self.panel_height = PANEL_HEIGHT
        self.special_characters = SPECIAL_CHARACTERS

        # Simple in-memory cache for images to avoid reloading
        self.cache = {}


    # === Helpers ===
    def _load_image(self, path: str) -> Image.Image:
        # --- Loads an image from cache or disk and return a PIL Image object ---
        self._validate_str("path", path)
        
        if path in self.cache:
            return self.cache[path].copy()
        
        if not os.path.exists(path): # File check
            raise FileNotFoundError(f"[Loader]: Missing image: {path}")
        
        try:
            img = Image.open(path).convert("RGBA")
        except Exception as e:
            raise RuntimeError(f"[Loader]: Failed to load {path} ({e})")
        
        self.cache[path] = img
        return img.copy()

    def _validate_stage(self, stage: str, base: str, turn: int | None = None, question_num: int | None = None) -> str:
        # --- Builds valid path based on stage, base, question number and turn ---
        self._validate_str("stage", stage)
        self._validate_str("base", base)
        self._validate_int("question_num", question_num, range(1,7), allow_none=True)
        self._validate_int("turn", turn, range(1,3), allow_none=True)

        if base not in ("assets", "answers"):
            raise ValueError(f"[Loader]: Invalid base input, is: {base}")
        
        base_path = getattr(self, f"{base}_path")

        if stage == "elimination": # Elimination stage pathing
            if base == "answers":
                if question_num is None:
                    raise ValueError(f"[Loader]: Invalid question_num input - {base} requires question_num")
                return os.path.join(base_path, stage, f"q{question_num}")
            return os.path.join(base_path, stage)
        
        elif stage == "final": # Final stage pathing
            if turn is None:
                raise ValueError(f"[Loader]: Invalid turn input - final stage requires turn")
            if base == "answers":
                if question_num is None:
                    raise ValueError(f"[Loader]: Invalid question_num input - {base} requires question_num")
                return os.path.join(base_path, stage, f"q{question_num}", f"turn{turn}")
            return os.path.join(base_path, stage, f"turn{turn}")
        
        else:
            raise ValueError(f"[Loader]: Invalid stage input - must be 'elimination' or 'final', is: {stage}")

    def _validate_int(self, name: str, value: int, valid_range: range | None = None, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be None")
            return

        if not isinstance(value, int): # Type check
            raise TypeError(f"[Loader]: Expected int {name}, got: {type(value)}")
        if valid_range is not None and value not in valid_range: # Value check
            raise ValueError(f"[Loader]: Invalid {name} input - '{name}' must be in range {list(valid_range)}, is: {value}")
    
    def _validate_str(self, name: str, value: str, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, str): # Type check
            raise TypeError(f"[Loader]: Expected str {name}, got: {type(value)}")
        
        if not value.strip():
            raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be empty")
        
    def _validate_bool(self, name: str, value: bool, expected_value: bool | None = None, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, bool): # Type check
            raise TypeError(f"[Loader]: Expected bool {name}, got: {type(value)}")
        if expected_value is not None and value != expected_value: # Value check
            raise ValueError(f"[Loader]: Invalid {name} - expected {expected_value}, got: {value}")

    def _generate_ordinal_numbers(self, num_answers: int) -> list[Image.Image]:
        # --- Generates a list of ordinal numbers images based on number of answers ---
        self._validate_int("num_answers", num_answers, range(1,7))
        
        num_img = []
        for i in range(1, num_answers+1):
            num_img.append(self.get_char(str(i)))
        return num_img


    # === Layout ===
    def load_layout(self, stage: str, num_answers: int | None = None, turn: int | None = None) -> dict[int, Image.Image]:
        # --- Loads a layout of answers placeholders and "sum" for given stage
        
        self._validate_int("num_answers", num_answers, range(1,7))

        folder_path = self._validate_stage(stage, "assets", turn)
        layout = {}
        for i in range(1, num_answers + 1):
            path = os.path.join(folder_path, f"a{i}.png")
            layout[i] = self._load_image(path)
        
        layout["numbers"] = self._generate_ordinal_numbers(num_answers)
       
        # For final stage, sum.png is in the parent folder (final/) not in turn subfolders
        if stage == "final":
            sum_path = os.path.join(self.assets_path, "final", "sum.png")
            layout["sum"] = self._load_image(sum_path)
        else:
            layout["sum"] = self._load_image(os.path.join(folder_path, "sum.png"))
        
        return layout


    # === Assets ===
    def load_asset(self, filename: str) -> Image.Image:
        # --- Loads a single asset ---
        self._validate_str("filename", filename)

        path = os.path.join(self.assets_path, f"{filename}.png")
        return self._load_image(path)


    # === Answers ===
    def get_answer(self, stage: str, question_num: int, answer_num: int, turn: int | None = None) -> tuple[Image.Image, str]:
        # --- Loads a specific answer image and return it with its path ---
        self._validate_int("answer_num", answer_num, range(1,7))
        
        folder_path = self._validate_stage(stage, "answers", turn, question_num)
        pattern = os.path.join(folder_path, f"a{answer_num}_*.png")
        files = glob.glob(pattern)
        if not files:
            raise FileNotFoundError(f"[Loader]: Missing files for pattern: {pattern}")
        
        path = files[0]
        img = self._load_image(path)
        return img, path


    # === Mistakes ===
    def get_x(self, big: bool, turn: int, mistake_num: int | None) -> Image.Image:
        # --- Loads a correct X image based on wheter it is big or not, turn and mistake number ---
        self._validate_bool("big", big)
        self._validate_int("turn", turn, range(1,3))
        self._validate_int("mistake_num", mistake_num, range(1,4), allow_none=True)
        
        if big:
            filename = f"x_big_{turn}.png"
        else:
            filename = f"{mistake_num}_x_small_{turn}.png"

        path = os.path.join(self.mistakes_path, filename)
        return self._load_image(path)


    # === Chars ===
    def get_char(self, char: str) -> Image.Image:
        # --- Loads an image representing a single character ---
        self._validate_str("char", char)
        
        if len(char) != 1: # Value check
            raise ValueError(f"[Loader]: Invalid character input - char's length must equal 1, is: {len(char)}")
        
        if char in self.special_characters:
            path = os.path.join(self.chars_path, self.special_characters[char])
        else:
            path = os.path.join(self.chars_path, f"{char.upper()}.png")

        return self._load_image(path)
    
    def get_space(self) -> Image.Image:
        # --- Returns transparent image for spacing ---
        return Image.new("RGBA", (self.panel_width, self.panel_height), (0, 0, 0, 0))
    

    # === Points ===
    def get_points(self, path: str) -> int:
        # --- Extracts points value from filename ---
        self._validate_str("path", path)
        
        filename = os.path.basename(path)
        match = re.search(r'_(\d+)\.png$', filename)
        if not match: # Value check
            raise ValueError(f"[Loader]: Missing matches for filename: {filename}")
        
        return int(match.group(1))


    # === Sounds ===
    def load_sound(self, sound_name: str) -> pygame.mixer.Sound:
        # --- Loads a sound file from data/sounds and returns a pygame Sound object ---
        self._validate_str("sound_name", sound_name)
        
        # Try both .wav and .mp3 extensions
        for ext in [".wav", ".mp3"]:
            path = os.path.join(self.sounds_path, f"{sound_name}{ext}")
            if os.path.exists(path):
                try:
                    sound = pygame.mixer.Sound(path)
                    return sound
                except Exception as e:
                    raise RuntimeError(f"[Loader]: Failed to load sound {path} ({e})")
        
        return sound