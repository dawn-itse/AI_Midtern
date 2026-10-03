"""Giao diện Pygame cho trận Sokoban đối kháng hai tác tử."""
from __future__ import annotations
from pathlib import Path
import agent_opponent
import agent_team
from competitive_core import CompetitiveGame
PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MAP = PROJECT_DIR / "maps" / "battle_map.txt"
class CompetitiveController:
    """Điều phối hai agent trên cùng trạng thái trước lượt và gọi engine."""

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
        # Hai agent phải chọn đồng thời trước khi engine áp dụng hành động nào.
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
    """Vẽ bàn cờ vừa khít vùng hiển thị và dùng màu dễ phân biệt."""
    COLORS = {1: (68, 166, 255), 2: (255, 95, 92), None: (232, 177, 79)}
    BACKGROUND = (10, 15, 23)
    FLOOR_A = (29, 38, 49)
    FLOOR_B = (32, 42, 54)
    WALL = (57, 72, 91)

    def __init__(self, screen, game, pygame_module):
        self.screen = screen
        self.game = game
        self.pygame = pygame_module
        self.cell_size = 1
        self.origin = (0, 0)
        self.board_rect = pygame_module.Rect(0, 0, 1, 1)

    @staticmethod
    def fit_grid(area_width, area_height, rows, columns):
        """Tính cạnh ô theo giới hạn vùng để mọi kích thước map đều vừa."""
        if rows <= 0 or columns <= 0:
            return 1
        return max(1, min(area_width // columns, area_height // rows))

    def rect(self, pos):
        row, col = pos
        return self.pygame.Rect(self.origin[0] + col * self.cell_size,
                                self.origin[1] + row * self.cell_size,
                                self.cell_size, self.cell_size)

    def draw(self, state, area=None):
        pygame = self.pygame
        if area is None:
            width, height = self.screen.get_size()
            area = pygame.Rect(20, 100, max(1, width - 40), max(1, height - 130))
        rows, columns = self.game.grid_rows, self.game.grid_cols
        self.cell_size = self.fit_grid(area.width, area.height, rows, columns)
        board_width, board_height = columns * self.cell_size, rows * self.cell_size
        self.origin = (area.x + (area.width - board_width) // 2,
                       area.y + (area.height - board_height) // 2)
        self.board_rect = pygame.Rect(self.origin[0], self.origin[1],
                                      board_width, board_height)
        # Nền riêng giúp lưới còn rõ khi map nhỏ nằm giữa vùng rộng.
        pygame.draw.rect(self.screen, (18, 25, 35), self.board_rect.inflate(12, 12),
                         border_radius=8)
        for row in range(rows):
            for col in range(columns):
                pos = (row, col)
                tile = self.rect(pos)
                if pos in state.walls:
                    pygame.draw.rect(self.screen, self.WALL, tile)
                    inset = max(1, self.cell_size // 9)
                    pygame.draw.line(self.screen, (93, 111, 133),
                                     (tile.left + inset, tile.top + inset),
                                     (tile.right - inset, tile.top + inset), max(1, inset // 2))
                else:
                    color = self.FLOOR_A if (row + col) % 2 == 0 else self.FLOOR_B
                    pygame.draw.rect(self.screen, color, tile)
                    pygame.draw.rect(self.screen, (39, 50, 63), tile, 1)

        for goal in state.goals:
            tile = self.rect(goal)
            radius = max(1, self.cell_size // 4)
            pygame.draw.circle(self.screen, (113, 88, 49), tile.center, radius + 2)
            pygame.draw.circle(self.screen, (245, 190, 89), tile.center, radius, 2)
            pygame.draw.circle(self.screen, (245, 190, 89), tile.center,
                               max(2, radius // 5))

        for pos, owner in state.boxes.items():
            tile = self.rect(pos)
            margin = max(1, self.cell_size // 8)
            block_size = max(1, self.cell_size - 2 * margin)
            offset = (self.cell_size - block_size) // 2
            block = pygame.Rect(tile.x + offset, tile.y + offset, block_size, block_size)
            color = self.COLORS[owner]
            pygame.draw.rect(self.screen, (8, 12, 18), block.move(1, max(2, margin // 2)),
                             border_radius=max(2, self.cell_size // 10))
            pygame.draw.rect(self.screen, color, block,
                             border_radius=max(2, self.cell_size // 10))
            pygame.draw.rect(self.screen, self._shade(color, 0.62), block, 2,
                             border_radius=max(2, self.cell_size // 10))
            pygame.draw.line(self.screen, self._shade(color, 1.18),
                             (block.left + margin // 2, block.top + margin // 2),
                             (block.right - margin // 2, block.top + margin // 2),
                             max(1, margin // 2))

        for agent_id, pos in state.agent_positions.items():
            tile = self.rect(pos)
            color = self.COLORS[agent_id]
            radius = max(1, self.cell_size // 3)
            pygame.draw.circle(self.screen, (8, 12, 18),
                               (tile.centerx + 1, tile.centery + 2), radius + 1)
            pygame.draw.circle(self.screen, color, tile.center, radius)
            pygame.draw.circle(self.screen, (235, 244, 255), tile.center,
                               max(2, radius // 2), max(1, self.cell_size // 14))

    @staticmethod
    def _shade(color, scale):
        return tuple(max(0, min(255, int(channel * scale))) for channel in color)
class CompetitiveGUI:
    WIDTH = 1120
    HEIGHT = 780

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
        self.title_font = None
        self.label_font = None
        self.clock = None
        self.max_steps_text = str(max_steps)
        self.editing_limit = False
        self.button_rects = {}
        self.panel_rect = None
        self.board_area = None
        self.limit_label_rect = None

    def initialize(self, create_window=True):
        pygame = self.pygame
        pygame.init()
        self.screen = (pygame.display.set_mode((self.WIDTH, self.HEIGHT)) if create_window
                       else pygame.Surface((self.WIDTH, self.HEIGHT)))
        if create_window:
            pygame.display.set_caption("Sokoban | Tactical Arena")
        self.renderer = CompetitiveRenderer(self.screen, self.controller.game, pygame)
        self.font = pygame.font.SysFont("segoeui", 24)
        self.small_font = pygame.font.SysFont("segoeui", 17)
        self.title_font = pygame.font.SysFont("segoeui", 31, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", 13, bold=True)
        self.clock = pygame.time.Clock()
        self._make_buttons()
        return self

    def _make_buttons(self):
        """Tạo các vùng bấm dựa trên kích thước cửa sổ hiện tại."""
        pygame = self.pygame
        width, height = self.screen.get_size()
        margin = max(14, min(24, width // 35))
        panel_width = min(292, max(228, width // 4))
        side_layout = width >= 820 and height >= 560
        if side_layout:
            panel_x = width - margin - panel_width
            self.panel_rect = pygame.Rect(panel_x, 112, panel_width, max(1, height - 240))
            self.board_area = pygame.Rect(margin, 112,
                                          max(1, panel_x - 2 * margin),
                                          max(1, height - 240))
            y = self.panel_rect.y + 169
            gap = 10
            button_height = 43
            half_width = (panel_width - 3 * gap) // 2
            self.button_rects = {
                "Step": pygame.Rect(panel_x + gap, y, half_width, button_height),
                "Run / Pause": pygame.Rect(panel_x + 2 * gap + half_width, y,
                                            half_width + 1, button_height),
                "Start / Reset": pygame.Rect(panel_x + gap, y + button_height + 10,
                                              panel_width - 2 * gap, button_height),
                "Step limit": pygame.Rect(panel_x + gap, self.panel_rect.y + 93,
                                           panel_width - 2 * gap, 40),
            }
            self.limit_label_rect = (panel_x + gap, self.panel_rect.y + 68)
        else:
            # Cửa sổ hẹp chuyển bảng điều khiển xuống dưới để không đè lên bản đồ.
            panel_height = min(205, max(150, height // 3))
            self.panel_rect = pygame.Rect(margin, max(112, height - panel_height - 16),
                                          max(1, width - 2 * margin), panel_height)
            self.board_area = pygame.Rect(margin, 100, max(1, width - 2 * margin),
                                          max(1, self.panel_rect.y - 112))
            y = self.panel_rect.y + panel_height - 54
            gap = 8
            button_width = max(1, (self.panel_rect.width - 4 * gap) // 3)
            self.button_rects = {
                "Step": pygame.Rect(margin + gap, y, button_width, 42),
                "Run / Pause": pygame.Rect(margin + 2 * gap + button_width, y,
                                            button_width, 42),
                "Start / Reset": pygame.Rect(margin + 3 * gap + 2 * button_width,
                                              y, button_width, 42),
                "Step limit": pygame.Rect(margin + gap, self.panel_rect.y + 48,
                                           max(1, min(160, self.panel_rect.width - 2 * gap)), 38),
            }
            self.limit_label_rect = (margin + gap, self.panel_rect.y + 24)
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

    def _draw_text(self, text, font, color, position, anchor="topleft"):
        rendered = font.render(str(text), True, color)
        rect = rendered.get_rect()
        setattr(rect, anchor, position)
        self.screen.blit(rendered, rect)
        return rect

    def _draw_panel(self, state):
        pygame = self.pygame
        panel = self.panel_rect
        pygame.draw.rect(self.screen, (18, 25, 35), panel, border_radius=12)
        pygame.draw.rect(self.screen, (43, 56, 71), panel, 1, border_radius=12)
        self._draw_text("MATCH CONTROL", self.label_font, (138, 158, 181),
                         (panel.x + 14, panel.y + 14))
        limit_box = self.button_rects["Step limit"]
        label_x, label_y = self.limit_label_rect
        self._draw_text("STEP LIMIT", self.label_font, (146, 165, 188), (label_x, label_y))
        pygame.draw.rect(self.screen, (25, 35, 47), limit_box, border_radius=7)
        outline = (86, 166, 255) if self.editing_limit else (57, 74, 94)
        pygame.draw.rect(self.screen, outline, limit_box, 2, border_radius=7)
        self._draw_text(self.max_steps_text, self.font, (238, 245, 252),
                         (limit_box.x + 12, limit_box.centery), "midleft")
        self._draw_text("turns", self.small_font, (117, 137, 159),
                         (limit_box.right - 12, limit_box.centery), "midright")

        labels = {"Step": "STEP", "Run / Pause": "PAUSE" if self.controller.running else "RUN",
                  "Start / Reset": "RESET MATCH"}
        for key, rect in self.button_rects.items():
            if key == "Step limit":
                continue
            primary = key == "Run / Pause"
            fill = (37, 104, 166) if primary else (34, 46, 60)
            edge = (76, 164, 244) if primary else (61, 79, 99)
            pygame.draw.rect(self.screen, fill, rect, border_radius=7)
            pygame.draw.rect(self.screen, edge, rect, 1, border_radius=7)
            self._draw_text(labels[key], self.label_font, (242, 247, 252), rect.center, "center")

        step_text = f"STEP  {state.current_step:>3} / {state.max_steps}"
        self._draw_text(step_text, self.font, (229, 238, 247),
                         (panel.x + 14, self.button_rects["Start / Reset"].bottom + 23))
        action_y = self.button_rects["Start / Reset"].bottom + 61
        self._draw_text("LAST ACTIONS", self.label_font, (138, 158, 181),
                         (panel.x + 14, action_y))
        self._draw_text(f"A1  {self.controller.last_actions[1]}", self.small_font,
                         self.COLORS[1], (panel.x + 14, action_y + 22))
        self._draw_text(f"A2  {self.controller.last_actions[2]}", self.small_font,
                         self.COLORS[2], (panel.x + 14, action_y + 45))
    COLORS = CompetitiveRenderer.COLORS
    def draw(self):
        pygame = self.pygame
        state = self.controller.game.state
        width, height = self.screen.get_size()
        self.screen.fill(CompetitiveRenderer.BACKGROUND)
        self._make_buttons()
        margin = max(14, min(24, width // 35))
        # Header tách trạng thái trận khỏi bàn cờ để người xem nhận biết nhanh.
        self._draw_text("SOKOBAN", self.title_font, (238, 245, 252), (margin, 18))
        title_width = self.title_font.size("SOKOBAN")[0]
        self._draw_text("TACTICAL ARENA", self.label_font, (99, 177, 239),
                         (margin + title_width + 12, 31))
        status_label = "RUNNING" if self.controller.running else (
            "COMPLETE" if self.controller.game.is_game_over() else "PAUSED / READY")
        status_color = (91, 211, 154) if self.controller.running else (160, 177, 196)
        self._draw_text(status_label, self.label_font, status_color,
                         (width - margin, 27), "topright")
        # Hai thẻ điểm luôn dùng màu riêng, không phụ thuộc vị trí trên bản đồ.
        card_width, card_height, gap = 142, 56, 12
        cards_right = width - margin
        cards_y = 45
        for agent_id, name in ((1, "AGENT 1"), (2, "AGENT 2")):
            x = cards_right - card_width
            card = pygame.Rect(x, cards_y, card_width, card_height)
            color = self.COLORS[agent_id]
            pygame.draw.rect(self.screen, (19, 27, 38), card, border_radius=8)
            pygame.draw.rect(self.screen, color, card, 1, border_radius=8)
            self._draw_text(name, self.label_font, color, (x + 10, cards_y + 8))
            self._draw_text(state.scores[agent_id], self.font, (244, 248, 252),
                             (x + 10, cards_y + 27))
            cards_right = x - gap

        self.renderer.draw(state, self.board_area)
        self._draw_panel(state)

        footer_y = height - 79
        pygame.draw.line(self.screen, (37, 49, 63), (margin, footer_y),
                         (width - margin, footer_y), 1)
        completed = state.scores[1] + state.scores[2]
        self._draw_text(f"SCORED BOXES  {completed}", self.label_font,
                         (144, 164, 186), (margin, footer_y + 13))
        status = self.controller.status
        self._draw_text(status, self.small_font, (215, 191, 133),
                         (margin, footer_y + 36))
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
