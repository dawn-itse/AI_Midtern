import pygame

class Renderer:
    def __init__(self, screen, problem, cell_size=60):
        self.screen = screen
        self.problem = problem
        self.cell_size = cell_size

        self.margin = 20

        max_row = 0
        max_col = 0

        all_positions = (
            set(problem.walls)
            | set(problem.targets)
            | set(problem.initial_state[1])
            | {problem.initial_state[0]}
        )

        for row, col in all_positions:
            max_row = max(max_row, row)
            max_col = max(max_col, col)

        self.map_height = max_row + 1
        self.map_width = max_col + 1

    def position_to_pixel(self, position):
        row, col = position

        x = self.margin + col * self.cell_size
        y = self.margin + row * self.cell_size

        return x, y

    def draw(self, state):
        self.screen.fill((30, 30, 30))

        agent_pos, box_positions = state

        for row in range(self.map_height):
            for col in range(self.map_width):
                position = (row, col)

                x, y = self.position_to_pixel(position)

                rect = pygame.Rect(
                    x,
                    y,
                    self.cell_size,
                    self.cell_size
                )

                if position in self.problem.walls:
                    pygame.draw.rect(
                        self.screen,
                        (70, 70, 70),
                        rect
                    )
                else:
                    pygame.draw.rect(
                        self.screen,
                        (220, 220, 220),
                        rect
                    )

                pygame.draw.rect(
                    self.screen,
                    (100, 100, 100),
                    rect,
                    1
                )

        for target in self.problem.targets:
            x, y = self.position_to_pixel(target)

            center = (
                x + self.cell_size // 2,
                y + self.cell_size // 2
            )

            pygame.draw.circle(
                self.screen,
                (240, 200, 60),
                center,
                self.cell_size // 5
            )

        for box in box_positions:
            x, y = self.position_to_pixel(box)

            rect = pygame.Rect(
                x + 8,
                y + 8,
                self.cell_size - 16,
                self.cell_size - 16
            )

            if box in self.problem.targets:
                pygame.draw.rect(
                    self.screen,
                    (70, 180, 90),
                    rect
                )
            else:
                pygame.draw.rect(
                    self.screen,
                    (180, 120, 60),
                    rect
                )

        x, y = self.position_to_pixel(agent_pos)

        center = (
            x + self.cell_size // 2,
            y + self.cell_size // 2
        )

        pygame.draw.circle(
            self.screen,
            (70, 130, 220),
            center,
            self.cell_size // 3
        )