# renderer/pygame_display.py
import pygame, sys

class PygameRenderer:
    def __init__(self, width=10, height=20, cell=20, caption="Tetris"):
        self.width = width
        self.height = height
        self.cell = cell
        pygame.init()
        self.screen = pygame.display.set_mode((width*cell, height*cell))
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

    def available(self):
        return True

    def render(self, buffer2d):
        # buffer2d: 2D array of (r,g,b) tuples, shape [height][width]
        self.screen.fill((0,0,0))
        for y in range(self.height):
            for x in range(self.width):
                color = buffer2d[y][x] if buffer2d[y][x] else (0,0,0)
                pygame.draw.rect(
                    self.screen, color,
                    (x*self.cell, y*self.cell, self.cell-1, self.cell-1)
                )
        pygame.display.flip()
