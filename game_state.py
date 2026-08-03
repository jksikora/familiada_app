ELIMINATION_ROUNDS_CONFIG = {
    1: 5,
    2: 4,
    3: 5,
    4: 5,
    5: 6,
    6: 5
}

class GameState:
    def __init__(self):
        self.elimination_rounds_config = ELIMINATION_ROUNDS_CONFIG

        # Stage control
        self.current_stage = "home"
        #self.current_stage = "elimination_over"
        #self.current_question_num = 1 #max 6
        self.current_question_num = 5
        self.current_num_answers = self.elimination_rounds_config[self.current_question_num]
        self.current_answer_num = 1 #max 6

        # Turn and points
        self.team_points = {1: 0, 2: 0}
        #self.team_points = {1: 100, 2: 150}  # DEBUG: Add some test points
        self.current_turn = 1 #or 2
        self.mistakes = 0 #max 3
        self.current_sum = 0

        # --- Elimination control ---
        self.is_round_active = False
        self.awaiting_steal = False
        self.revealed_elimination_answers: dict[int, list[bool]] = {}

        # --- Final control ---
        self.final_answers = {1: [None] * 6, 2: [None] * 6}
        self.revealed_final_answers: dict[int, list[bool]] = {}
        self.final_turn_switched = False

    # === Helpers ===
    def _validate_int(self, name: str, value: int, valid_range: range | None = None, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[GameState]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, int): # Type check
            raise TypeError(f"[GameState]: Expected int {name}, got: {type(value)}")
        if valid_range is not None and value not in valid_range: # Value check
            raise ValueError(f"[GameState]: Invalid {name} input - '{name}' must be in range {list(valid_range)}, is: {value}")
    
    def _validate_str(self, name: str, value: str, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[GameState]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, str): # Type check
            raise TypeError(f"[GameState]: Expected str {name}, got: {type(value)}")
        
        if not value.strip():
            raise ValueError(f"[Loader]: Invalid {name} input - {name} cannot be empty")
    
    def _validate_bool(self, name: str, value: bool, expected_value: bool | None = None, allow_none: bool = False) -> None:
        if value is None:
            if not allow_none:
                raise ValueError(f"[GameState]: Invalid {name} input - {name} cannot be None")
            return
        
        if not isinstance(value, bool): # Type check
            raise TypeError(f"[GameState]: Expected bool {name}, got: {type(value)}")
        if expected_value is not None and value != expected_value: # Value check
            raise ValueError(f"[Loader]: Invalid {name} - expected {expected_value}, got: {value}")

    def _validate_stage(self, expected: str) -> None:
        if self.current_stage != expected: # Runtime check
            raise RuntimeError(f"[GameState]: Invalid stage - expected '{expected}', got: '{self.current_stage}'")


    # === Elimination Stage ===
    def start_elimination_round(self, question_num: int, turn: int = 1) -> None:
        self._validate_int("question_num", question_num, range(1, 7))
        self._validate_int("turn", turn, range(1, 3))
        
        self.current_stage = "elimination"
        self.current_question_num = question_num
        self.current_num_answers = self.elimination_rounds_config[question_num]
        self.current_turn = turn
        self.mistakes = 0
        self.current_sum = 0
        self.awaiting_steal = False
        self.is_round_active = True

        self.revealed_elimination_answers[question_num] = [False] * self.current_num_answers

    def record_elimination_answer(self, answer_num: int, points: int) -> None:
        self._validate_stage("elimination")
        self._validate_int("answer_num", answer_num, range(1,7))
        if points < 0: # Value check
            raise ValueError(f"[GameState]: Invalid points input - points must be positive, is: {points}")
        question_num = self.current_question_num
        if question_num not in self.revealed_elimination_answers:
            raise ValueError(f"[GameState]: Invalid question_num input - question {question_num} not initialized")
        revealed_answers = self.revealed_elimination_answers[question_num]
        if revealed_answers[answer_num - 1]:
            raise ValueError(f"[GameState]: Invalid answer_num input - answer {answer_num} already revealed")
        
        revealed_answers[answer_num - 1] = True
        self.current_sum += points

    def record_mistake(self) -> None:
        self._validate_bool("is_round_active", self.is_round_active, expected_value=True)

        self.mistakes += 1
        if self.mistakes == 3:
            self.awaiting_steal = True
            self.is_round_active = False
    
    def attempt_steal(self, is_correct: bool) -> None:
        self._validate_bool("is_correct", is_correct)
        self._validate_bool("awaiting_steal", self.awaiting_steal, expected_value=True)

        stealing_turn = 2 if self.current_turn == 1 else 1
        if is_correct:
            self.team_points[stealing_turn] += self.current_sum
        else:
            self.team_points[self.current_turn] += self.current_sum
    
    def end_elimination_round(self) -> None:
        # Award points to current team if round ended normally (not during steal)
        if not self.awaiting_steal and self.current_sum > 0:
            self.team_points[self.current_turn] += self.current_sum
        
        self.is_round_active = False
        self.awaiting_steal = False
        self.current_sum = 0

    # def next_elimination_question(self, turn: int, is_round_active: bool) -> bool:
    #     self._validate_int("turn", turn, range(1,3))
    #     self._validate_bool("is_round_active", is_round_active, expected_value=False)
    #     if self.current_question_num >= len(self.elimination_rounds_config):
    #         return False
        
    #     self.current_question_num += 1
    #     self.start_elimination_round(self.current_question_num, turn)
    #     return True


    # === Final Stage ===
    def start_final_stage(self) -> None:
        self.current_stage = "final"
        self.current_question_num = 1
        self.current_sum = 0
        self.current_turn = 1
        self.final_answers = {1: [None] * 6, 2: [None] * 6}
        self.revealed_final_answers[self.current_turn] = [False] * 6
        self.final_turn_switched = False
    
    def record_final_answer(self, turn: int, question_num: int, answer: int, points: int) -> None:
        self._validate_stage("final")
        self._validate_int("turn", turn, range(1, 3))
        self._validate_int("question_num", question_num, range(1, 7))
        self._validate_int("points", points)

        if self.final_answers[turn][question_num - 1] is not None: # Value check
            raise ValueError(f"[GameState]: Invalid question_num input - {question_num} already answered.")

        self.final_answers[turn][question_num - 1] = (answer, points)

    def record_custom_final_answer(self, turn: int, question_num: int, answer: str, points: int = 0) -> None:
        self._validate_stage("final")
        self._validate_int("turn", turn, range(1, 3))
        self._validate_int("question_num", question_num, range(1, 7))
        self._validate_str("answer", answer)
        self._validate_int("points", points)

        if self.final_answers[turn][question_num - 1] is not None: # Value check
            raise ValueError(f"[GameState]: Invalid question_num input - {question_num} already answered.")

        self.final_answers[self.current_turn][question_num - 1] = (answer, points)

    def next_final_question(self) -> bool:
        turn = self.current_turn
        unanswered = [i + 1 for i, v in enumerate(self.final_answers[turn]) if v is None]
        if not unanswered:
            return False

        higher = [i for i in unanswered if i > self.current_question_num]
        if higher:
            self.current_question_num = min(higher)
        else:
            self.current_question_num = min(unanswered)

        return True

    def end_final_round(self) -> None:
        for i, answer in enumerate(self.final_answers[self.current_turn]):
            if answer is None:
                self.final_answers[self.current_turn][i] = ("_"*11, 0)

    def reveal_final_answer(self, question_num: int) -> None:
        self._validate_int("question_num", question_num, range(1,7))

        revealed_answers = self.revealed_final_answers[self.current_turn]
        if revealed_answers[question_num - 1]:
            raise ValueError(f"[GameState]: Invalid question_num input - answer {question_num} already revealed")
        
        revealed_answers[question_num - 1] = True
        # Add points to sum only when the answer is revealed
        ans = self.final_answers[self.current_turn][question_num - 1]
        if ans is not None:
            _, pts = ans
            self.current_sum += int(pts)

    def switch_final_turn(self) -> None:
        self.current_turn = 2
        self.current_question_num = 1
        self.final_turn_switched = True

    def is_answer_duplicate(self, answer: str, question_num: int) -> bool:
        self._validate_str("answer", answer)
        self._validate_int("question_num", question_num, range(1, 7))
        if self.current_turn != 2:
            raise RuntimeError(f"[GameState]: Invalid operation - current_turn must equal 2, is: {self.current_turn}")

        # Get player 1's answer for this specific question
        player1_answer = self.final_answers[1][question_num - 1]
        if player1_answer is None:
            return False
        
        player1_value, _ = player1_answer
        
        # Skip comparison if player 1's answer is a placeholder
        if isinstance(player1_value, str) and player1_value.startswith("_"):
            return False
        
        # Normalize player 2's input: digits compared as ints, others as strings
        key = int(answer) if answer.isdigit() else answer
        
        return key == player1_value
    

    # === Reset ===
    def reset_game(self) -> None:
        self.__init__()
        
