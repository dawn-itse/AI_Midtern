import pygame

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, 28)
    def draw(self, screen):
        pygame.draw.rect(
            screen,
            (60, 60, 60),
            self.rect
        )

        pygame.draw.rect(
            screen,
            (180, 180, 180),
            self.rect,
            2
        )

        text_surface = self.font.render(
            self.text,
            True,
            (255, 255, 255)
        )

        text_rect = text_surface.get_rect(
            center=self.rect.center
        )

        screen.blit(
            text_surface,
            text_rect
        )
    def is_clicked(self, position):
        return self.rect.collidepoint(position)