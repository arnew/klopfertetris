# main.py
import time
import pygame
from tetris_core import TetrisGame, PIECE_COLORS
from renderer.usb_frame import try_open, send_frame

WIDTH = 10
HEIGHT = 20
PIXEL_SIZE = 24   # onscreen pixel size for pygame window

KEY_LEFT  = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_DOWN  = pygame.K_DOWN
KEY_ROT   = pygame.K_UP
KEY_DROP  = pygame.K_SPACE
KEY_QUIT  = pygame.K_ESCAPE

def build_composite(game: TetrisGame):
    board = game.board
    piece_buf = game.get_buffer()
    ghost_buf = game.get_ghost_buffer()
    preview_buf = game.get_preview_overlay()

    frame = []
    for y in range(HEIGHT):
        row = []
        for x in range(WIDTH):
            cell = piece_buf[y][x] or board[y][x] or preview_buf[y][x] or ghost_buf[y][x]
            if cell:
                base = PIECE_COLORS[cell.upper()]
                if cell.islower():
                    base = (base[0]//4, base[1]//4, base[2]//4)
                row.append(base)
            else:
                row.append((0,0,0))
        frame.append(row)
    return frame

def draw_pygame(screen, frame):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r,g,b = frame[y][x]
            pygame.draw.rect(
                screen,
                (r,g,b),
                (x*PIXEL_SIZE, y*PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE)
            )
    pygame.display.flip()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH * PIXEL_SIZE, HEIGHT * PIXEL_SIZE))
    pygame.display.set_caption("Klopferlight Tetris (Hybrid Output)")

    usb = try_open()
    if usb:
        print("USB output enabled on:", usb.port)
    else:
        print("No USB Klopferlight detected → using pygame display only")

    game = TetrisGame(WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    fall_timer = 0.0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        fall_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == KEY_QUIT:
                    running = False
                elif event.key == KEY_LEFT:
                    game.move(-1, 0)
                elif event.key == KEY_RIGHT:
                    game.move(+1, 0)
                elif event.key == KEY_ROT:
                    game.rotate()
                elif event.key == KEY_DROP:
                    game.hard_drop()

        keys = pygame.key.get_pressed()
        if keys[KEY_DOWN]:
            game.soft_drop()
        else:
            if fall_timer >= game.fall_speed:
                game.fall()
                fall_timer = 0.0

        frame = build_composite(game)

        # Send to Klopferlight if attached
        if usb:
            send_frame(usb, frame, WIDTH, HEIGHT)

        # Always draw to pygame window
        draw_pygame(screen, frame)

    pygame.quit()

if __name__ == "__main__":
    main()
