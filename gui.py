import pygame

from sokoban_core import SokobanProblem
from ucs import UCSSolver
from astar import AStarSolver
from renderer import Renderer
from button import Button


class Game:
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

    def solve(self, algo="UCS"):
        """Giải bài toán với thuật toán được chọn (UCS hoặc A*)."""
        self.algo_used = algo
        if algo == "A*":
            solver = AStarSolver(self.problem)
        else:
            solver = UCSSolver(self.problem)

        result = solver.search()

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
            next_state = self.get_next_state(
                current_state,
                action
            )

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


class SokobanGUI:
    def __init__(self, problem):
        pygame.init()

        self.problem = problem
        self.game = Game(problem)

        self.screen_width = 800
        self.screen_height = 700

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )

        pygame.display.set_caption("Sokoban - AI Search (UCS & A*)")

        self.renderer = Renderer(
            self.screen,
            problem
        )

        button_y = 620

        self.backward_button = Button(
            120,
            button_y,
            150,
            45,
            "Backward (<-)"
        )

        self.pause_button = Button(
            325,
            button_y,
            150,
            45,
            "Pause (Space)"
        )

        self.forward_button = Button(
            530,
            button_y,
            150,
            45,
            "Forward (->)"
        )

        # Hai nút chọn thuật toán UCS và A* trên giao diện (Yêu cầu 5)
        self.ucs_button = Button(
            480,
            560,
            135,
            38,
            "Solve UCS (U)"
        )

        self.astar_button = Button(
            635,
            560,
            135,
            38,
            "Solve A* (A)"
        )

        self.font = pygame.font.SysFont(
            None,
            28
        )

        self.clock = pygame.time.Clock()

    def draw_information(self):
        step_text = (
            f"Actions: {self.game.current_step} / "
            f"{len(self.game.states) - 1}"
        )

        text_surface = self.font.render(
            step_text,
            True,
            (255, 255, 255)
        )

        self.screen.blit(
            text_surface,
            (20, 568)
        )

        pause_text = " [PAUSED]" if self.game.paused else " [RUNNING]"
        if self.game.solved:
            status = f"Solved ({self.game.algo_used}){pause_text}"
        else:
            status = "Choose UCS (U) or A* (A)"

        status_surface = self.font.render(
            status,
            True,
            (255, 220, 100) if self.game.solved else (200, 200, 200)
        )

        self.screen.blit(
            status_surface,
            (180, 568)
        )

    def handle_event(self, event):
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

        if event.type == pygame.KEYDOWN:
            # Nhấn U hoặc S để chạy UCS
            if event.key in (pygame.K_s, pygame.K_u):
                self.game.solve("UCS")

            # Nhấn A để chạy A*
            elif event.key == pygame.K_a:
                self.game.solve("A*")

            # Nhấn Right để đi tới bước tiếp theo
            elif event.key == pygame.K_RIGHT:
                self.game.forward()

            # Nhấn Left để quay lại bước trước
            elif event.key == pygame.K_LEFT:
                self.game.backward()

            # Nhấn Space để Pause / Resume
            elif event.key == pygame.K_SPACE:
                self.game.toggle_pause()

        return True

    def draw(self):
        self.renderer.draw(
            self.game.current_state
        )

        self.draw_information()

        # Vẽ các nút điều khiển
        self.backward_button.draw(self.screen)
        self.pause_button.draw(self.screen)
        self.forward_button.draw(self.screen)

        # Vẽ các nút chọn thuật toán
        self.ucs_button.draw(self.screen)
        self.astar_button.draw(self.screen)

        pygame.display.flip()

    def run(self):
        running = True
        step_timer = 0

        while running:
            dt = self.clock.tick(60)

            for event in pygame.event.get():
                running = self.handle_event(event)

            # Tự động bước đi (Animation) nếu đã giải và không bị Pause
            if self.game.solved and not self.game.paused:
                step_timer += dt
                if step_timer >= 350:  # 350ms mỗi bước
                    if self.game.current_step < len(self.game.states) - 1:
                        self.game.forward()
                    else:
                        self.game.paused = True  # Đã đi đến bước cuối cùng
                    step_timer = 0

            self.draw()

        pygame.quit()