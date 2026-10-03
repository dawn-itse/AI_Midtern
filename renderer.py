import pygame

class Renderer:
    def __init__(self, screen, problem, cell_size=None):
        self.screen = screen
        self.problem = problem

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

        screen_w = self.screen.get_width() if self.screen else 800
        screen_h = self.screen.get_height() if self.screen else 700
        max_board_w = screen_w - 40
        max_board_h = 510  # Khu vực phía trên thanh điều khiển

        # Tự động co giãn kích thước ô (cell_size) sao cho toàn bộ bản đồ luôn vừa khít màn hình
        if cell_size is not None:
            self.cell_size = cell_size
        else:
            fit_w = max_board_w // max(1, self.map_width)
            fit_h = max_board_h // max(1, self.map_height)
            self.cell_size = max(20, min(60, fit_w, fit_h))

        # Căn giữa bàn cờ trong khung hình
        total_board_w = self.map_width * self.cell_size
        total_board_h = self.map_height * self.cell_size
        self.margin_x = max(20, (screen_w - total_board_w) // 2)
        self.margin_y = 20 + max(0, (max_board_h - total_board_h) // 2)

    def position_to_pixel(self, position):
        row, col = position

        x = self.margin_x + col * self.cell_size
        y = self.margin_y + row * self.cell_size

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

            box_pad = max(4, self.cell_size // 7)
            rect = pygame.Rect(
                x + box_pad,
                y + box_pad,
                self.cell_size - 2 * box_pad,
                self.cell_size - 2 * box_pad
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