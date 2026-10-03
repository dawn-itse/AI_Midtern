"""Pygame viewer for the existing simultaneous two-agent game engine."""

from __future__ import annotations

from pathlib import Path

import agent_opponent
import agent_team
from competitive_core import CompetitiveGame


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MAP = PROJECT_DIR / "maps" / "battle_map.txt"


class CompetitiveController:
    """Coordinates agents against one shared pre-turn snapshot and calls the engine."""

    def __init__(self, map_path=DEFAULT_MAP, max_steps=30):
        self.map_path = self._resolve_map(map_path)
        self.max_steps = max(1, int(max_steps))
        self.game = CompetitiveGame(str(self.map_path), self.max_steps)
        self.status = "Ready. Enter a step limit and press Start."
        self.running = False
        self.last_actions = {1: "Stay", 2: "Stay"}

    @staticmethod
    def _resolve_map(map_path):
        path = Path(map_path).expanduser()
        if path.is_absolute():
            return path.resolve()
        cwd_path = (Path.cwd() / path).resolve()
        if cwd_path.is_file():
            return cwd_path
        return (PROJECT_DIR / path).resolve()

    def start(self, max_steps=None):
        if max_steps is not None:
            self.max_steps = max(1, int(max_steps))
        self.game = CompetitiveGame(str(self.map_path), self.max_steps)
        self.last_actions = {1: "Stay", 2: "Stay"}
        self.running = False
        self.status = "Match ready. Step once or start automatic play."

    def play_turn(self, force=False):
        if (not self.running and not force) or self.game.is_game_over():
            self.running = False
            self.status = self._result_text()
            return False
        shared_state = self.game.get_state()
        # Both choices are computed before the engine applies either one.
        action1 = agent_team.get_action(shared_state.clone(), 1, time_limit_ms=1000)
        action2 = agent_opponent.get_action(shared_state.clone(), 2, time_limit_ms=1000)
        if action1 not in self.game.get_legal_actions(1, shared_state):
            action1 = "Stay"
        if action2 not in self.game.get_legal_actions(2, shared_state):
            action2 = "Stay"
        self.last_actions = {1: action1, 2: action2}
        self.game.step(action1, action2)
        if self.game.is_game_over():
            self.running = False
            self.status = self._result_text()
        else:
            self.status = f"Last turn: Agent 1 {action1}; Agent 2 {action2}."
        return True

    def toggle_run(self):
        if self.game.is_game_over():
            self.status = self._result_text()
            self.running = False
        else:
            self.running = not self.running
            self.status = "Simulation running." if self.running else "Simulation paused."

    def _result_text(self):
        winner = self.game.get_winner()
        if winner is None:
            return (f"Draw at step {self.game.state.current_step}: "
                    f"{self.game.state.scores[1]}–{self.game.state.scores[2]}")
        return (f"Agent {winner} wins at step {self.game.state.current_step}: "
                f"{self.game.state.scores[1]}–{self.game.state.scores[2]}")


class CompetitiveRenderer:
    COLORS = {1: (54, 137, 220), 2: (220, 92, 80), None: (177, 139, 82)}

    def __init__(self, screen, game, pygame_module):
        self.screen = screen
        self.game = game
        self.pygame = pygame_module
        self.cell_size = max(24, min(54, 700 // max(game.grid_rows, game.grid_cols, 1)))
        self.origin = (24, 76)

    def rect(self, pos):
        row, col = pos
        return self.pygame.Rect(self.origin[0] + col * self.cell_size,
                                self.origin[1] + row * self.cell_size,
                                self.cell_size, self.cell_size)

    def draw(self, state):
        pygame = self.pygame
        self.screen.fill((28, 32, 40))
        for row in range(self.game.grid_rows):
            for col in range(self.game.grid_cols):
                pos = (row, col)
                rect = self.rect(pos)
                pygame.draw.rect(self.screen, (68, 75, 88) if pos in state.walls
                                 else (225, 227, 230), rect)
                pygame.draw.rect(self.screen, (145, 150, 160), rect, 1)
        for goal in state.goals:
            rect = self.rect(goal)
            pygame.draw.circle(self.screen, (194, 72, 72), rect.center,
                               max(4, self.cell_size // 7))
        for pos, owner in state.boxes.items():
            rect = self.rect(pos).inflate(-self.cell_size // 5, -self.cell_size // 5)
            pygame.draw.rect(self.screen, self.COLORS[owner], rect, border_radius=4)
        for agent_id, pos in state.agent_positions.items():
            rect = self.rect(pos)
            pygame.draw.circle(self.screen, self.COLORS[agent_id], rect.center,
                               self.cell_size // 3)


class CompetitiveGUI:
    WIDTH = 960
    HEIGHT = 760

    def __init__(self, map_path=DEFAULT_MAP, max_steps=50, pygame_module=None):
        if pygame_module is None:
            try:
                import pygame as pygame_module
            except ImportError as exc:
                raise RuntimeError("Pygame is required. Install dependencies with pip install -r requirements.txt") from exc
        self.pygame = pygame_module
        self.controller = CompetitiveController(map_path, max_steps)
        self.screen = None
        self.renderer = None
        self.font = None
        self.small_font = None
        self.clock = None
        self.max_steps_text = str(max_steps)
        self.editing_limit = False
        self.button_rects = {}

    def initialize(self, create_window=True):
        pygame = self.pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT)) if create_window else pygame.Surface((self.WIDTH, self.HEIGHT))
        if create_window:
            pygame.display.set_caption("Sokoban — Competitive")
        self.renderer = CompetitiveRenderer(self.screen, self.controller.game, pygame)
        self.font = pygame.font.SysFont(None, 30)
        self.small_font = pygame.font.SysFont(None, 23)
        self.clock = pygame.time.Clock()
        self._make_buttons()
        return self

    def _make_buttons(self):
        pygame = self.pygame
        self.button_rects = {
            "Step": pygame.Rect(24, self.HEIGHT - 60, 96, 40),
            "Run / Pause": pygame.Rect(132, self.HEIGHT - 60, 140, 40),
            "Start / Reset": pygame.Rect(282, self.HEIGHT - 60, 140, 40),
            "Step limit": pygame.Rect(430, 22, 112, 38),
        }

    def _start_match(self):
        try:
            steps = int(self.max_steps_text)
            if steps < 1:
                raise ValueError
        except ValueError:
            self.controller.status = "Enter a positive integer step limit."
            return
        self.controller.start(steps)

    def handle_event(self, event):
        pygame = self.pygame
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rects["Step limit"].collidepoint(event.pos):
                self.editing_limit = True
                return True
            self.editing_limit = False
            for label, rect in self.button_rects.items():
                if label != "Step limit" and rect.collidepoint(event.pos):
                    if label == "Step":
                        self.controller.play_turn(force=True)
                    elif label == "Run / Pause":
                        self.controller.toggle_run()
                    elif label == "Start / Reset":
                        self._start_match()
                    break
        if event.type == pygame.KEYDOWN:
            if self.editing_limit:
                if event.key == pygame.K_RETURN:
                    self.editing_limit = False
                elif event.key == pygame.K_BACKSPACE:
                    self.max_steps_text = self.max_steps_text[:-1]
                elif getattr(event, "unicode", "").isdigit():
                    self.max_steps_text += event.unicode
            elif event.key == pygame.K_SPACE:
                self.controller.toggle_run()
            elif event.key in (pygame.K_RIGHT, pygame.K_RETURN):
                self.controller.play_turn(force=True)
        return True

    def draw(self):
        pygame = self.pygame
        state = self.controller.game.state
        self.renderer.draw(state)
        score = self.font.render(
            f"Step {state.current_step}/{state.max_steps}    "
            f"Agent 1: {state.scores[1]}    Agent 2: {state.scores[2]}",
            True, (245, 245, 245))
        self.screen.blit(score, (24, 18))
        self.screen.blit(self.small_font.render("Step limit n:", True, (245, 245, 245)), (420, 31))
        box = self.button_rects["Step limit"]
        pygame.draw.rect(self.screen, (55, 65, 80), box, border_radius=4)
        self.screen.blit(self.small_font.render(self.max_steps_text, True, (255, 255, 255)), (box.x + 12, box.y + 9))
        detail = self.small_font.render(
            f"Completed boxes on goals: {state.scores[1] + state.scores[2]}    "
            f"Last actions: A1 {self.controller.last_actions[1]} / A2 {self.controller.last_actions[2]}",
            True, (235, 235, 235))
        self.screen.blit(detail, (24, self.HEIGHT - 100))
        status = self.small_font.render(self.controller.status, True, (255, 218, 130))
        self.screen.blit(status, (24, self.HEIGHT - 78))
        self._make_buttons()
        for label, rect in self.button_rects.items():
            if label == "Step limit":
                continue
            pygame.draw.rect(self.screen, (65, 72, 84), rect, border_radius=5)
            pygame.draw.rect(self.screen, (180, 185, 195), rect, 1, border_radius=5)
            text = self.small_font.render(label, True, (250, 250, 250))
            self.screen.blit(text, text.get_rect(center=rect.center))
        if pygame.display.get_surface() is not None:
            pygame.display.flip()

    def tick(self):
        if self.controller.running:
            self.controller.play_turn()
        self.draw()
        if self.clock:
            self.clock.tick(4 if self.controller.running else 30)

    def run(self):
        if self.screen is None:
            self.initialize()
        running = True
        while running:
            for event in self.pygame.event.get():
                running = self.handle_event(event)
            self.tick()
        self.pygame.quit()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", nargs="?", default=str(DEFAULT_MAP), help="Đường dẫn bản đồ thi đấu")
    parser.add_argument("steps", nargs="?", type=int, default=50, help="Số bước tối đa n")
    args = parser.parse_args()
    CompetitiveGUI(args.map, max_steps=args.steps).run()


if __name__ == "__main__":
    main()
