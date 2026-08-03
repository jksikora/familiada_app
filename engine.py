from loader import Loader
from game_state import GameState
from renderer import Renderer
from gui import GUI
import time

class Engine:
    def __init__(self, loader: Loader, gamestate: GameState, renderer: Renderer, gui: GUI):
        self.loader = loader
        self.gamestate = gamestate
        self.renderer = renderer
        self.gui = gui

    def handle_command(self, command: str):
        stage = self.gamestate.current_stage

        # Home Stage
        if stage == "home":
            if command == "enter":
                self.gui.set_message("Press 'enter' to confirm start.")
                self.gamestate.current_stage = "home_confirm"
            else:
                self.gui.set_message("Invalid command. Press 'enter' to start.")

        elif stage == "home_confirm":
            if command == "enter":
                self.gui.set_message("Elimination round 1. Choose team: 1 or 2.")
                self.gamestate.start_elimination_round(1, 1) # Default to team 1 just to initialize
                self.renderer.draw_elimination_layout(
                    self.gamestate.current_num_answers,
                    self.gamestate.team_points,
                    self.gamestate.current_sum
                )
                self.gamestate.current_stage = "elimination_start"
                self.renderer.play_sound("elimination_round_starts")
            else:
                self.gamestate.current_stage = "home"


        # Elimination Stage
        elif stage == "elimination_start":
            if command in ("1", "2"):
                turn = int(command)
                self.gamestate.start_elimination_round(self.gamestate.current_question_num, turn)
                self.gui.set_message(f"Elimination round {self.gamestate.current_question_num}. Team {turn} starts. Type answer number or 'x' for mistake.")
                self.renderer.draw_elimination_layout(
                    self.gamestate.current_num_answers,
                    self.gamestate.team_points,
                    self.gamestate.current_sum
                )
                return
            else:
                self.gui.set_message("Invalid command. Type '1' or '2' to select team.")

        elif stage == "elimination":
            if self.gamestate.is_round_active and not self.gamestate.awaiting_steal:
                if command.isdigit() and 1 <= int(command) <= self.gamestate.current_num_answers:
                    try:
                        _, path = self.loader.get_answer("elimination", self.gamestate.current_question_num, int(command))
                        points = self.loader.get_points(path)
                        self.gamestate.record_elimination_answer(int(command), points)
                        self.renderer.draw_answer("elimination", self.gamestate.current_question_num, int(command))
                        self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                        self.renderer.play_sound("correct")
                        self.gui.set_message(f"Answer {command} revealed. +{points} points.")
                        self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                        
                        # Check if all answers are revealed
                        if all(self.gamestate.revealed_elimination_answers[self.gamestate.current_question_num]):
                            self.gamestate.end_elimination_round()
                            self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                            self.renderer.draw_team_points(self.gamestate.team_points)
                            
                            # Show appropriate message based on whether there are more rounds
                            if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                                self.gui.set_message(f"Elimination round {self.gamestate.current_question_num} is over. Type 'next' for next question.")
                            else:
                                self.gui.set_message("Elimination stage is over. Type 'next' for final stage.")
                    except ValueError:
                        self.gui.set_message(f"Answer {command} already revealed. Choose a different answer.")
                
                elif command == "x":
                    self.gamestate.record_mistake()
                    self.renderer.draw_mistake(False, self.gamestate.current_turn, self.gamestate.mistakes)
                    self.renderer.play_sound("wrong")
                    self.gui.set_message(f"Mistake {self.gamestate.mistakes}/3.")
                    if self.gamestate.mistakes == 3:
                        self.gui.set_message("Stealing phase. Team switches. Type answer number or 'x' for mistake.")
                
                elif command == "next":
                    self.gui.set_message("You can only go to the next round after the current round is finished.")

                else:
                    self.gui.set_message("Invalid command. Type number or 'x' for mistake.")
                return
            
            elif not self.gamestate.is_round_active and not self.gamestate.awaiting_steal:
                if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                    if command == "next":
                        self.gamestate.current_stage = "elimination_start"
                        self.gamestate.current_question_num += 1
                        self.gui.set_message(f"Elimination round {self.gamestate.current_question_num}. Choose team: 1 or 2.")
                        self.renderer.draw_elimination_layout(
                            self.gamestate.elimination_rounds_config[self.gamestate.current_question_num],
                            self.gamestate.team_points,
                            0
                        )
                        self.renderer.play_sound("elimination_round_starts")
                    else:
                        self.gui.set_message(f"Elimination round {self.gamestate.current_question_num} is over. Type 'next' for next question.")
                else:
                    if command == "next":
                        # Start final stage immediately on last elimination
                        self.gamestate.start_final_stage()
                        self._init_final_timer()
                        self.renderer.draw_final_layout(
                            self.gamestate.current_turn,
                            self.gamestate.current_sum
                        )
                        self.renderer.play_sound("final_starts")
                        self.gui.set_message("Final stage started. Type 'start' for player 1.")
                        return
                    else:
                        self.gui.set_message("Elimination stage is over. Type 'next' for final stage.")
                return

            if self.gamestate.awaiting_steal:
                if command.isdigit() and 1 <= int(command) <= self.gamestate.current_num_answers:
                    try:
                        _, path = self.loader.get_answer("elimination", self.gamestate.current_question_num, int(command))
                        points = self.loader.get_points(path)
                        self.gamestate.record_elimination_answer(int(command), points)
                        self.renderer.draw_answer("elimination", self.gamestate.current_question_num, int(command))
                        self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                        self.renderer.play_sound("correct")
                        self.gui.set_message(f"Answer {command} revealed. +{points} points.")
                        self.gamestate.attempt_steal(True)
                        self.gamestate.end_elimination_round()
                        self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                        self.renderer.draw_team_points(self.gamestate.team_points)
                        
                        # Check if all answers are now revealed
                        if all(self.gamestate.revealed_elimination_answers[self.gamestate.current_question_num]):
                            # All answers revealed, skip reveal phase
                            if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                                self.gui.set_message(f"Steal successful. Sum goes to team {2 if self.gamestate.current_turn == 1 else 1}. Elimination round {self.gamestate.current_question_num} is over. Type 'next' for next question.")
                            else:
                                self.gui.set_message(f"Steal successful. Sum goes to team {2 if self.gamestate.current_turn == 1 else 1}. Elimination stage is over. Type 'next' to start the final stage.")
                        else:
                            # Some answers still unrevealed, go to reveal phase
                            self.gui.set_message(f"Steal successful. Sum goes to team {2 if self.gamestate.current_turn == 1 else 1}. Elimination round {self.gamestate.current_question_num} is over. Type '>' to reveal answers.")
                            self.gamestate.current_stage = "elimination_reveal"
                    except ValueError:
                        self.gui.set_message(f"Answer {command} already revealed. Choose a different answer.")
                
                elif command == "x":
                    self.renderer.draw_mistake(True, 2 if self.gamestate.current_turn == 1 else 1)
                    self.renderer.play_sound("wrong")
                    self.gamestate.attempt_steal(False)
                    self.gamestate.end_elimination_round()
                    self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                    self.renderer.draw_team_points(self.gamestate.team_points)
                    
                    # Check if all answers are now revealed
                    if all(self.gamestate.revealed_elimination_answers[self.gamestate.current_question_num]):
                        # All answers revealed, skip reveal phase
                        if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                            self.gui.set_message(f"Steal failed. Sum goes to team {self.gamestate.current_turn}. Elimination round {self.gamestate.current_question_num} is over. Type 'next' for next question.")
                        else:
                            self.gui.set_message(f"Steal failed. Sum goes to team {self.gamestate.current_turn}. Elimination stage is over. Type 'next' to start the final stage.")
                    else:
                        # Some answers still unrevealed, go to reveal phase
                        self.gui.set_message(f"Steal failed. Sum goes to team {self.gamestate.current_turn}. Elimination round {self.gamestate.current_question_num} is over. Type '>' to reveal answers.")
                        self.gamestate.current_stage = "elimination_reveal"
                else:
                    self.gui.set_message("Invalid command. Type number or 'x' for mistake.")
                return
            
        elif stage == "elimination_reveal":
            if command == ">":
                answers = self.gamestate.revealed_elimination_answers[self.gamestate.current_question_num]
                for answer_num, revealed in enumerate(answers):
                    if not revealed:
                        self.renderer.draw_answer("elimination", self.gamestate.current_question_num, answer_num + 1)
                        self.renderer.play_sound("correct")
                        answers[answer_num] = True
                        
                        # Check if this was the last answer to reveal
                        remaining = sum(1 for a in answers if not a)
                        if remaining == 0:
                            # All answers now revealed
                            if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                                self.gui.set_message(f"Answer {answer_num + 1} revealed. Elimination round {self.gamestate.current_question_num} is over. Type 'next' for next question.")
                            else:
                                self.gui.set_message(f"Answer {answer_num + 1} revealed. Elimination stage is over. Type 'next' for final stage.")
                        else:
                            self.gui.set_message(f"Answer {answer_num + 1} revealed. Type '>' to reveal next answer.")
                        break
                else:
                    # All answers revealed, check if there are more rounds
                    if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                        self.gamestate.current_stage = "elimination_start"
                        self.gamestate.current_question_num += 1
                        self.gui.set_message(f"Elimination round {self.gamestate.current_question_num}. Choose team: 1 or 2.")
                        self.renderer.draw_elimination_layout(
                            self.gamestate.elimination_rounds_config[self.gamestate.current_question_num],
                            self.gamestate.team_points,
                            0
                        )
                    else:
                        # Stay in reveal stage; 'next' now starts final directly
                        self.gui.set_message("Elimination stage is over. Type 'next' for final stage.")
            
            elif command == "next":
                # Check if all answers are revealed before allowing 'next'
                answers = self.gamestate.revealed_elimination_answers[self.gamestate.current_question_num]
                if all(answers):
                    # All answers revealed, proceed to next round
                    if self.gamestate.current_question_num < len(self.gamestate.elimination_rounds_config):
                        self.gamestate.current_stage = "elimination_start"
                        self.gamestate.current_question_num += 1
                        self.gui.set_message(f"Elimination round {self.gamestate.current_question_num}. Choose team: 1 or 2.")
                        self.renderer.draw_elimination_layout(
                            self.gamestate.elimination_rounds_config[self.gamestate.current_question_num],
                            self.gamestate.team_points,
                            0
                        )
                        self.renderer.play_sound("elimination_round_starts")
                    else:
                        # Last elimination question completed in reveal; start final immediately
                        self.gamestate.start_final_stage()
                        self._init_final_timer()
                        self.renderer.draw_final_layout(
                            self.gamestate.current_turn,
                            self.gamestate.current_sum
                        )
                        self.renderer.play_sound("final_starts")
                        self.gui.set_message("Final stage started. Type 'start' for player 1.")
                else:
                    self.gui.set_message("Not all answers revealed yet. Use '>' to reveal answers.")
            
            else:
                self.gui.set_message("Invalid command. Use '>' to reveal answers.")

        


        # Final Stage
        elif stage == "final":
            if not self.timer_active and not self.final_timer_expired:
                if command == "start":
                    self.timer_duration = 15 if self.gamestate.current_turn == 1 else 20
                    self.timer_start = time.time()
                    self.timer_active = True
                    self.time_left = self.timer_duration
                    self.renderer.draw_timer(self.time_left)
                    self.gui.set_message(f"Timer started. {self.time_left} seconds left.")
                else:
                    self.gui.set_message("Invalid input. Type 'start' to begin answering.")
                return

            # Only allow answer input if timer is active and not expired
            if self.timer_active and not self.final_timer_expired:
                if command.isdigit() and 1 <= int(command) <= 6:
                    if self.gamestate.current_turn == 2:
                        if self.gamestate.is_answer_duplicate(command, self.gamestate.current_question_num):
                            self.renderer.play_sound("repeated")
                            self.gui.set_message(f"Duplicate answer! Player 1 already gave this answer for question {self.gamestate.current_question_num}.")
                            return
                    try:
                        _, path = self.loader.get_answer("final", self.gamestate.current_question_num, int(command), self.gamestate.current_turn)
                        points = self.loader.get_points(path)
                    except FileNotFoundError:
                        self.gui.set_message(f"No asset for answer {command}. Type text or choose another number.")
                        return
                    except Exception:
                        self.gui.set_message(f"Could not load answer {command}. Choose another or type text.")
                        return
                    self.gamestate.record_final_answer(self.gamestate.current_turn, self.gamestate.current_question_num, int(command), points)
                    self.gui.set_message(f"Recorded answer {command} for question {self.gamestate.current_question_num}.")
                    has_next = self.gamestate.next_final_question()
                    if not has_next:
                        self.timer_active = False
                        self.final_timer_expired = True
                        self.gamestate.end_final_round()
                        self.gamestate.current_stage = "final_reveal"
                        self.gui.set_message("All questions answered. Reveal answers with '>'")

                elif command == "s":
                    has_next = self.gamestate.next_final_question()
                    if has_next:
                        self.gui.set_message(f"Skipped. Next question: {self.gamestate.current_question_num}.")

                elif len(command) > 1 and command not in ("enter", "next", "start"):
                    if self.gamestate.current_turn == 2:
                        if self.gamestate.is_answer_duplicate(command, self.gamestate.current_question_num):
                            self.renderer.play_sound("repeated")
                            self.gui.set_message(f"Duplicate answer! Player 1 already gave this answer for question {self.gamestate.current_question_num}.")
                            return
                        
                    self.gamestate.record_custom_final_answer(self.gamestate.current_turn, self.gamestate.current_question_num, command)
                    self.gui.set_message(f"Recorded custom answer for question {self.gamestate.current_question_num}.")
                    has_next = self.gamestate.next_final_question()
                    if not has_next:
                        self.timer_active = False
                        self.final_timer_expired = True
                        self.gamestate.end_final_round()
                        self.gamestate.current_stage = "final_reveal"
                        self.gui.set_message("All questions answered. Reveal answers with '>'.")
                else:
                    self.gui.set_message("Invalid command. Type answer, number or 's' to skip.")
                return

            if self.final_timer_expired and self.gamestate.current_turn == 1:
                if command == "next":
                    self.renderer.clear_timer()
                    self.gamestate.switch_final_turn()
                    self._init_final_timer()
                    self.gui.set_message("Player 2's turn. Type 'start'.")
                else:
                    self.gui.set_message("Invalid command. Use 'next' to start the second final round.")
                return
            
            elif self.final_timer_expired and self.gamestate.current_turn == 2:
                if command == "next":
                    self.gamestate.current_stage = "end"
                    self.renderer.draw_end_screen(self.gamestate.current_sum)
                    self.gui.set_message("Game over. Press 'enter' to quit or 'start' to reset.")
                else:
                    self.gui.set_message("Invalid command. Use 'next' to end.")
                return
            
        elif stage == "final_reveal":
            if command == ">":
                revealed = self.gamestate.revealed_final_answers[self.gamestate.current_turn]
                answers = self.gamestate.final_answers[self.gamestate.current_turn]
                for question_num, is_revealed in enumerate(revealed):
                    if not is_revealed:
                        answer, points = answers[question_num]
                        if points > 0:
                            self.renderer.draw_answer("final", question_num + 1, answer, self.gamestate.current_turn)
                            self.renderer.play_sound("correct")
                        elif points == 0:
                            self.renderer.draw_custom_answer("final", self.gamestate.current_turn, question_num + 1, answer, points)
                            self.renderer.play_sound("wrong")
                        self.gamestate.reveal_final_answer(question_num + 1)
                        self.renderer.draw_sum(self.gamestate.current_sum, self.gamestate.current_stage)
                        remaining = sum(1 for r in revealed if not r)
                        if remaining == 0:
                            if self.gamestate.current_turn == 1:
                                self.gui.set_message(f"Answer for {question_num + 1} revealed. Type 'next' to start player 2.")
                            else:
                                self.gui.set_message(f"Answer for {question_num + 1} revealed. Type 'next' to end.")
                        else:
                            self.gui.set_message(f"Answer for {question_num + 1} revealed. Type '>' to reveal next answer.")
                        break
                else:
                    # All answers for current turn revealed already; instruct next step
                    if self.gamestate.current_turn == 1:
                        self.gui.set_message("All answers revealed. Type 'next' to start player 2.")
                    else:
                        self.gui.set_message("All answers revealed. Type 'next' to end.")
            elif command == "next":
                # Allow 'next' once all answers are revealed
                revealed = self.gamestate.revealed_final_answers[self.gamestate.current_turn]
                if all(revealed):
                    if self.gamestate.current_turn == 1:
                        # Move to player 2 start
                        self.gamestate.switch_final_turn()
                        self._init_final_timer()
                        # Clear any lingering timer digits and redraw layout cleanly
                        self.renderer.clear_timer()
                        # Ensure turn 2 reveal tracking exists
                        if 2 not in self.gamestate.revealed_final_answers:
                            self.gamestate.revealed_final_answers[2] = [False] * 6
                        self.gamestate.current_stage = "final"
                        self.renderer.play_sound("final_round_ends")
                        self.gui.set_message("Player 2's turn. Type 'start'.")
                    else:
                        # End of game flow
                        self.gamestate.current_stage = "end"
                        self.renderer.draw_end_screen(self.gamestate.current_sum)
                        self.renderer.play_sound("familiada_theme")
                        self.gui.set_message("Game over. Press 'enter' to quit or 'start' to reset.")
                else:
                    self.gui.set_message("Not all answers revealed yet. Use '>' to reveal answers.")
            else:
                self.gui.set_message("Invalid command. Use '>' to reveal answers.")


        # End Stage
        elif stage == "end":
            if command == "enter":
                self.gui.set_message("Press enter to confirm quit.")
                self.gamestate.current_stage = "end_confirm"
                self.renderer.draw_end_screen(self.gamestate.current_sum)
            elif command == "start":
                self.gamestate.reset_game()
                self.gui.set_message("Game reset. Back to home screen.")
                self.renderer.draw_home_screen()
            else:
                self.gui.set_message("Invalid command. Press 'enter' to end or 'start' to reset.")
        
        elif stage == "end_confirm":
            if command == "enter":
                self.gui.set_message("Quitting game.")
                self.gui.running = False
            else:
                self.gui.set_message("Invalid command. Press 'enter' to confirm quit.")

    # Timer variables for final stage
    def _init_final_timer(self):
        self.timer_active = False
        self.timer_start = None
        self.timer_duration = 0
        self.time_left = 0
        self.final_timer_expired = False

    def update_final_timer(self):
        if self.gamestate.current_stage != "final":
            self._init_final_timer()
            return
        
        # Reset timer when the turn changes in the final stage
        if self.gamestate.final_turn_switched:
            self._init_final_timer()
            self.gamestate.final_turn_switched = False
            
        # Timer countdown
        if self.timer_active:
            elapsed = int(time.time() - self.timer_start)
            new_time_left = max(self.timer_duration - elapsed, 0)
            if new_time_left != self.time_left:
                self.time_left = new_time_left
                self.renderer.clear_timer()
                self.renderer.draw_timer(self.time_left)
            if self.time_left == 0 and not self.final_timer_expired:
                self.timer_active = False
                self.final_timer_expired = True
                self.gamestate.end_final_round()
                self.gamestate.current_stage = "final_reveal"
                self.gui.set_message("Time is up. Reveal answers with '>'.")