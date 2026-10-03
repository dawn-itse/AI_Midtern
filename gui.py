"""Giao diện Pygame cho trình diễn tìm kiếm Sokoban."""
from __future__ import annotations
import pygame
from sokoban_core import SokobanProblem
from ucs import UCSSolver
from astar import AStarSolver
from renderer import Renderer
from button import Button
class Game:
    """Lưu lời giải và trạng thái đang được trình diễn trên bàn cờ."""
    def __init__(self, problem):
        self.problem = problem
        self.solver = UCSSolver(problem)
        self.solution = []
        self.states = [problem.initial_state]
        self.current_step = 0
        self.current_state = problem.initial_state
        self.paused = False
        self.solved = False
        self.algo_used = "UCS"
        self.search_stats = None

    def solve(self, algo="UCS"):
        """Chạy solver đã chọn và lưu thống kê thực tế nếu solver cung cấp."""
        self.algo_used = algo
        if algo == "A*":
            solver = AStarSolver(self.problem)
        else:
            solver = UCSSolver(self.problem)
        self.solver = solver
        result = solver.search()
        self.search_stats = {
            "execution_time": getattr(solver, "execution_time", None),
            "nodes_explored": getattr(solver, "nodes_explored", None),
            "max_frontier_size": getattr(solver, "max_frontier_size", None),
        }

        if result is None:
            self.solution = []
            self.states = [self.problem.initial_state]
            self.current_step = 0
            self.current_state = self.problem.initial_state
            self.solved = False
            return False

        self.solution, _ = result
        self.states = [self.problem.initial_state]
        current_state = self.problem.initial_state
        for action in self.solution:
            next_state = self.get_next_state(current_state, action)
            if next_state is None:
                break
            self.states.append(next_state)
            current_state = next_state

        self.current_step = 0
        self.current_state = self.states[0]
        self.solved = True
        self.paused = False
        return True
    
    def get_next_state(self, state, action):
        successors = self.problem.get_successors(state)
        for successor_action, successor_state in successors:
            if successor_action == action:
                return successor_state
        return None

    def forward(self):
        if self.current_step < len(self.states) - 1:
            self.current_step += 1
            self.current_state = self.states[self.current_step]

    def backward(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.current_state = self.states[self.current_step]

    def toggle_pause(self):
        self.paused = not self.paused

    def reset_playback(self):
        """Đưa trình diễn về đầu lời giải mà không chạy lại thuật toán."""
        self.current_step = 0
        self.current_state = self.states[0]
        self.paused = True


class SokobanGUI:
    """Bố trí giao diện, nhận thao tác và trình diễn lời giải Sokoban."""

    WIDTH = 1120
    HEIGHT = 780
    BACKGROUND = (10, 15, 23)
    PANEL = (18, 25, 35)
    EDGE = (43, 56, 71)
    FLOOR_A = (29, 38, 49)
    FLOOR_B = (32, 42, 54)
    WALL = (57, 72, 91)
    BLUE = (68, 166, 255)
    GOLD = (245, 190, 89)

    def __init__(self, problem):
        pygame.init()
        self.problem = problem
        self.game = Game(problem)
        self.screen_width = self.WIDTH
        self.screen_height = self.HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Sokoban | Tactical Search")

        # Giữ renderer cũ để tương thích với các nơi đang tham chiếu thuộc tính này.
        self.renderer = Renderer(self.screen, problem)
        self.backward_button = Button(0, 0, 1, 1, "BACK")
        self.pause_button = Button(0, 0, 1, 1, "RUN")
        self.forward_button = Button(0, 0, 1, 1, "STEP")
        self.ucs_button = Button(0, 0, 1, 1, "SOLVE UCS")
        self.astar_button = Button(0, 0, 1, 1, "SOLVE A*")
        self.reset_button = Button(0, 0, 1, 1, "RESET")

        self.font = pygame.font.SysFont("segoeui", 22)
        self.small_font = pygame.font.SysFont("segoeui", 16)
        self.title_font = pygame.font.SysFont("segoeui", 31, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", 13, bold=True)
        self.clock = pygame.time.Clock()
        self.board_area = pygame.Rect(24, 112, 760, 560)
        self.panel_rect = pygame.Rect(804, 112, 292, 560)
        self.board_rect = pygame.Rect(0, 0, 0, 0)
        self.cell_size = 1
        self.board_origin = (0, 0)
        self._layout()

    @staticmethod
    def fit_grid(area_width, area_height, rows, columns):
        """Tính cạnh ô lớn nhất có thể vừa vùng bảng mà không cắt map."""
        if rows <= 0 or columns <= 0:
            return 1
        return max(1, min(area_width // columns, area_height // rows))

    def _layout(self):
        """Tính vùng board, thông tin và nút từ kích thước màn hình hiện tại."""
        width, height = self.screen.get_size()
        margin = max(16, min(24, width // 40))
        panel_width = min(310, max(250, width // 4))
        panel_x = width - margin - panel_width
        content_top = 112
        footer_height = 62
        content_height = max(1, height - content_top - footer_height - 20)
        self.panel_rect = pygame.Rect(panel_x, content_top, panel_width, content_height)
        self.board_area = pygame.Rect(margin, content_top,
                                      max(1, panel_x - margin * 2), content_height)

        inset = 14
        button_gap = 9
        button_height = 39
        button_width = (panel_width - inset * 2 - button_gap * 2) // 3
        buttons_y = self.panel_rect.bottom - inset - button_height
        self.backward_button.rect = pygame.Rect(panel_x + inset, buttons_y,
                                                button_width, button_height)
        self.pause_button.rect = pygame.Rect(panel_x + inset + button_width + button_gap,
                                             buttons_y, button_width, button_height)
        self.forward_button.rect = pygame.Rect(panel_x + inset + 2 * (button_width + button_gap),
                                               buttons_y, button_width, button_height)
        algo_y = buttons_y - button_height - 10
        algo_width = (panel_width - inset * 2 - button_gap) // 2
        self.ucs_button.rect = pygame.Rect(panel_x + inset, algo_y, algo_width, button_height)
        self.astar_button.rect = pygame.Rect(panel_x + inset + algo_width + button_gap,
                                             algo_y, algo_width, button_height)
        self.reset_button.rect = pygame.Rect(panel_x + inset, algo_y - button_height - 10,
                                             panel_width - inset * 2, button_height)

    def _draw_text(self, text, font, color, position, anchor="topleft"):
        rendered = font.render(str(text), True, color)
        rect = rendered.get_rect()
        setattr(rect, anchor, position)
        self.screen.blit(rendered, rect)
        return rect

    def _draw_board(self):
        """Vẽ từng lớp map riêng để đích và vật thể vẫn rõ trên ô nền tối."""
        rows, columns = self.renderer.map_height, self.renderer.map_width
        self.cell_size = self.fit_grid(self.board_area.width - 20,
                                       self.board_area.height - 20, rows, columns)
        board_width, board_height = columns * self.cell_size, rows * self.cell_size
        self.board_origin = (self.board_area.x + (self.board_area.width - board_width) // 2,
                             self.board_area.y + (self.board_area.height - board_height) // 2)
        self.board_rect = pygame.Rect(*self.board_origin, board_width, board_height)
        pygame.draw.rect(self.screen, self.PANEL, self.board_rect.inflate(14, 14),
                         border_radius=10)

        agent_position, box_positions = self.game.current_state
        for row in range(rows):
            for column in range(columns):
                position = (row, column)
                tile = pygame.Rect(self.board_origin[0] + column * self.cell_size,
                                   self.board_origin[1] + row * self.cell_size,
                                   self.cell_size, self.cell_size)
                if position in self.problem.walls:
                    pygame.draw.rect(self.screen, self.WALL, tile)
                    pad = max(1, self.cell_size // 9)
                    pygame.draw.line(self.screen, (91, 109, 131),
                                     (tile.left + pad, tile.top + pad),
                                     (tile.right - pad, tile.top + pad), max(1, pad // 2))
                else:
                    floor_color = self.FLOOR_A if (row + column) % 2 == 0 else self.FLOOR_B
                    pygame.draw.rect(self.screen, floor_color, tile)
                    pygame.draw.rect(self.screen, (39, 50, 63), tile, 1)

        for target in self.problem.targets:
            center = (self.board_origin[0] + target[1] * self.cell_size + self.cell_size // 2,
                      self.board_origin[1] + target[0] * self.cell_size + self.cell_size // 2)
            radius = max(1, self.cell_size // 4)
            pygame.draw.circle(self.screen, (113, 88, 49), center, radius + 2)
            pygame.draw.circle(self.screen, self.GOLD, center, radius, 2)
            pygame.draw.circle(self.screen, self.GOLD, center, max(1, radius // 5))

        for box in box_positions:
            x = self.board_origin[0] + box[1] * self.cell_size
            y = self.board_origin[1] + box[0] * self.cell_size
            margin = max(1, self.cell_size // 8)
            block_size = max(1, self.cell_size - 2 * margin)
            block = pygame.Rect(x + (self.cell_size - block_size) // 2,
                                y + (self.cell_size - block_size) // 2,
                                block_size, block_size)
            on_target = box in self.problem.targets
            color = (80, 194, 125) if on_target else (218, 151, 69)
            pygame.draw.rect(self.screen, (8, 12, 18), block.move(1, max(1, margin // 2)),
                             border_radius=max(2, self.cell_size // 10))
            pygame.draw.rect(self.screen, color, block,
                             border_radius=max(2, self.cell_size // 10))
            pygame.draw.rect(self.screen, (174, 235, 190) if on_target else (255, 203, 122),
                             block, 2, border_radius=max(2, self.cell_size // 10))

        center = (self.board_origin[0] + agent_position[1] * self.cell_size + self.cell_size // 2,
                  self.board_origin[1] + agent_position[0] * self.cell_size + self.cell_size // 2)
        radius = max(1, self.cell_size // 3)
        pygame.draw.circle(self.screen, (8, 12, 18), (center[0] + 1, center[1] + 2), radius + 1)
        pygame.draw.circle(self.screen, self.BLUE, center, radius)
        pygame.draw.circle(self.screen, (235, 244, 255), center,
                           max(1, radius // 2), max(1, self.cell_size // 14))

    def _draw_button(self, button, label, primary=False, active=False):
        """Vẽ trạng thái hover và chọn thuật toán mà Button cơ bản chưa hỗ trợ."""
        hovered = button.rect.collidepoint(pygame.mouse.get_pos())
        selected = active
        if primary or selected:
            fill = (37, 104, 166) if not hovered else (48, 125, 193)
            edge = (76, 164, 244)
        else:
            fill = (34, 46, 60) if not hovered else (47, 62, 80)
            edge = (61, 79, 99)
        pygame.draw.rect(self.screen, fill, button.rect, border_radius=7)
        pygame.draw.rect(self.screen, edge, button.rect, 1, border_radius=7)
        text = self.label_font.render(label, True, (242, 247, 252))
        self.screen.blit(text, text.get_rect(center=button.rect.center))

    def _draw_panel(self):
        panel = self.panel_rect
        pygame.draw.rect(self.screen, self.PANEL, panel, border_radius=12)
        pygame.draw.rect(self.screen, self.EDGE, panel, 1, border_radius=12)
        self._draw_text("SEARCH STATUS", self.label_font, (138, 158, 181),
                        (panel.x + 16, panel.y + 15))

        status = ("SOLUTION FOUND" if self.game.solved else "READY TO SOLVE")
        status_color = (91, 211, 154) if self.game.solved else (160, 177, 196)
        self._draw_text(status, self.small_font, status_color, (panel.x + 16, panel.y + 43))
        self._draw_text(f"ALGORITHM  {self.game.algo_used}", self.small_font,
                        (99, 177, 239), (panel.x + 16, panel.y + 72))

        info_y = panel.y + 113
        playback = "PAUSED" if self.game.paused else ("RUNNING" if self.game.solved else "IDLE")
        values = [("ACTIONS", f"{self.game.current_step} / {max(0, len(self.game.states) - 1)}"),
                  ("PLAYBACK", playback)]
        if self.game.search_stats is not None:
            stats = self.game.search_stats
            elapsed = stats["execution_time"]
            nodes = stats["nodes_explored"]
            frontier = stats["max_frontier_size"]
            if elapsed is not None:
                values.append(("SEARCH TIME", f"{elapsed:.3f} s"))
            if nodes is not None:
                values.append(("EXPANDED NODES", f"{nodes:,}"))
            if frontier is not None:
                values.append(("MAX FRONTIER", f"{frontier:,}"))

        for label, value in values:
            self._draw_text(label, self.label_font, (119, 141, 164),
                            (panel.x + 16, info_y))
            info_y += 19
            self._draw_text(value, self.font, (235, 242, 249),
                            (panel.x + 16, info_y))
            info_y += 37

        self._draw_button(self.reset_button, "RESET", active=False)
        self._draw_button(self.ucs_button, "SOLVE UCS", active=self.game.algo_used == "UCS")
        self._draw_button(self.astar_button, "SOLVE A*", active=self.game.algo_used == "A*")
        self.pause_button.text = "PAUSE" if not self.game.paused else "RUN"
        self._draw_button(self.pause_button, self.pause_button.text, primary=True)
        self._draw_button(self.backward_button, "BACK")
        self._draw_button(self.forward_button, "STEP")

    def draw_information(self):
        """Hiển thị lượt hiện tại và thông báo, không tự tạo số liệu tìm kiếm."""
        width, height = self.screen.get_size()
        margin = max(16, min(24, width // 40))
        footer_y = height - 53
        pygame.draw.line(self.screen, (37, 49, 63), (margin, footer_y),
                         (width - margin, footer_y), 1)
        if self.game.solved:
            message = f"{self.game.algo_used} solution · {len(self.game.solution)} actions"
        else:
            message = "Choose UCS or A* to search for a solution"
        self._draw_text(message, self.small_font, (215, 191, 133),
                        (margin, footer_y + 10))
        self._draw_text("U / S: UCS    A: A*    ← / →: step    SPACE: run / pause",
                        self.label_font, (119, 141, 164),
                        (width - margin, footer_y + 11), "topright")

    def handle_event(self, event):
        """Giữ các phím cũ và dùng cùng vùng nút cho thao tác chuột."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_position = event.pos
            if self.backward_button.is_clicked(mouse_position):
                self.game.backward()
            elif self.forward_button.is_clicked(mouse_position):
                self.game.forward()
            elif self.pause_button.is_clicked(mouse_position):
                self.game.toggle_pause()
            elif self.ucs_button.is_clicked(mouse_position):
                self.game.solve("UCS")
            elif self.astar_button.is_clicked(mouse_position):
                self.game.solve("A*")
            elif self.reset_button.is_clicked(mouse_position):
                self.game.reset_playback()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_s, pygame.K_u):
                self.game.solve("UCS")
            elif event.key == pygame.K_a:
                self.game.solve("A*")
            elif event.key == pygame.K_RIGHT:
                self.game.forward()
            elif event.key == pygame.K_LEFT:
                self.game.backward()
            elif event.key == pygame.K_SPACE:
                self.game.toggle_pause()
            elif event.key == pygame.K_r:
                self.game.reset_playback()
        return True

    def draw(self):
        """Vẽ lại giao diện từ trạng thái hiện tại sau mỗi lần xử lý sự kiện."""
        self._layout()
        self.screen.fill(self.BACKGROUND)
        width, height = self.screen.get_size()
        margin = max(16, min(24, width // 40))
        self._draw_text("SOKOBAN", self.title_font, (238, 245, 252), (margin, 17))
        title_width = self.title_font.size("SOKOBAN")[0]
        self._draw_text("TACTICAL SEARCH", self.label_font, (99, 177, 239),
                        (margin + title_width + 12, 30))
        header_status = "RUNNING" if not self.game.paused and self.game.solved else (
            "SOLVED" if self.game.solved else "READY")
        status_color = (91, 211, 154) if self.game.solved else (160, 177, 196)
        self._draw_text(header_status, self.label_font, status_color,
                        (width - margin, 27), "topright")

        # Board được căn giữa trong vùng còn lại sau khi dành không gian cho panel.
        self._draw_board()
        self._draw_panel()
        self.draw_information()
        pygame.display.flip()

    def run(self):
        running = True
        step_timer = 0
        while running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                running = self.handle_event(event)

            # Bước tự động chỉ chạy khi có lời giải và người dùng đã bật Run.
            if self.game.solved and not self.game.paused:
                step_timer += dt
                if step_timer >= 350:
                    if self.game.current_step < len(self.game.states) - 1:
                        self.game.forward()
                    else:
                        self.game.paused = True
                    step_timer = 0

            self.draw()
        pygame.quit()
