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
        self.screen.fill((0,0,0))
        for y in range(self.height):
            for x in range(self.width):
                v = buffer2d[y][x]
                if isinstance(v, tuple):
                    color = v
                else:
                    color = (255,128,0) if v else (0,0,0)
                if v:
                    pygame.draw.rect(self.screen, color, (x*self.cell, y*self.cell, self.cell-1, self.cell-1))
        pygame.display.flip()
