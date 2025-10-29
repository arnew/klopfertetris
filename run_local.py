# run_local_improved.py
import pygame, sys, time
from tetris_core import Game, PIECE_COLORS

CELL = 24
WIDTH = 10
HEIGHT = 20

# DAS parameters (seconds)
DAS_DELAY = 0.15   # initial delay before auto-repeat
DAS_REPEAT = 0.05  # repeat interval

pygame.init()
screen = pygame.display.set_mode((WIDTH*CELL + 160, HEIGHT*CELL))  # extra space for next preview
pygame.display.set_caption("Tetris Improved")
clock = pygame.time.Clock()

g = Game(width=WIDTH, height=HEIGHT, level=0, lock_delay=0.5)

# DAS state
left_held = False
right_held = False
left_next = 0
right_next = 0
last_left_time = 0
last_right_time = 0

def draw_board(surface, board_buf, ghost_buf, next_piece_type):
    # background
    surface.fill((8,8,8))
    # draw cells
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = board_buf[y][x]
            if v:
                color = PIECE_COLORS.get(v, (120,120,120))
                pygame.draw.rect(surface, color, (x*CELL, y*CELL, CELL-1, CELL-1))
    # draw ghost overlay (dim)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            v = ghost_buf[y][x]
            if v:
                base = PIECE_COLORS.get(v, (120,120,120))
                ghost_col = (base[0]//4, base[1]//4, base[2]//4)
                pygame.draw.rect(surface, ghost_col, (x*CELL, y*CELL, CELL-1, CELL-1))
    # next preview box
    nx = WIDTH*CELL + 10
    pygame.draw.rect(surface, (20,20,20), (nx, 10, 140, 140))
    font = pygame.font.SysFont(None, 24)
    txt = font.render("Next", True, (200,200,200))
    surface.blit(txt, (nx+10, 10))
    # draw next piece centered in box
    if next_piece_type:
        preview = TETROMINO_PREVIEWS[next_piece_type]
        # preview is 4x4 grid
        px0 = nx + 20
        py0 = 40
        for ry in range(4):
            for rx in range(4):
                if preview[ry][rx]:
                    color = PIECE_COLORS.get(next_piece_type, (200,200,200))
                    pygame.draw.rect(surface, color, (px0 + rx*CELL//2, py0 + ry*CELL//2, CELL//2-1, CELL//2-1))

# small previews (reuse same shapes scaled down)
TETROMINO_PREVIEWS = TETROMINOS = {
    'I': [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    'O': [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
    'T': [[0,1,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'J': [[1,0,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'L': [[0,0,1,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'S': [[0,1,1,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
    'Z': [[1,1,0,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
}

# helper: compute ghost buffer for rendering
def composite_buffers(board_buf, current_buf, ghost_buf):
    # board_buf: placed blocks, current_buf: showing falling piece, ghost_buf: ghost positions
    # we want to render placed blocks, then ghost (dim), then current piece (bright).
    # In our Game we have convenience methods; here, we call Game.get_buffer & get_ghost_buffer.
    pass

last = time.time()

while True:
    now = time.time()
    dt = now - last
    last = now

    # event handling (keyboard + quit)
    actions = {"left":False,"right":False,"rotate":False,"soft":False,"hard":False,"start":False,"quit":False}
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_LEFT:
                # immediate move + start DAS
                moved = g.move(-1)
                left_held = True
                left_next = now + DAS_DELAY
                last_left_time = now
            elif ev.key == pygame.K_RIGHT:
                moved = g.move(1)
                right_held = True
                right_next = now + DAS_DELAY
                last_right_time = now
            elif ev.key == pygame.K_UP:
                g.rotate()
            elif ev.key == pygame.K_DOWN:
                g.soft_drop()
            elif ev.key == pygame.K_SPACE:
                g.hard_drop()
            elif ev.key == pygame.K_RETURN:
                # restart if game over
                if g.game_over:
                    g.reset()
        elif ev.type == pygame.KEYUP:
            if ev.key == pygame.K_LEFT:
                left_held = False
            elif ev.key == pygame.K_RIGHT:
                right_held = False

    # DAS autorepeat handling
    if left_held:
        if now >= left_next:
            if g.move(-1):
                pass
            left_next = now + DAS_REPEAT
    if right_held:
        if now >= right_next:
            if g.move(1):
                pass
            right_next = now + DAS_REPEAT

    # Soft drop hold detection: use key state
    keys = pygame.key.get_pressed()
    soft_hold = keys[pygame.K_DOWN]

    g.update(dt, soft_down=soft_hold)

    buf = g.get_buffer()            # main buffer with falling piece
    ghost_buf = g.get_ghost_buffer()  # ghost positions
    # Draw: we want placed blocks + ghost as dim + falling piece on top
    # To make it simple, render placed blocks from board, draw ghost dim, then draw falling piece from get_buffer overlay.

    # build placed-only buffer from g.board
    placed_buf = [[0]*WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        for x in range(WIDTH):
            placed_buf[y][x] = g.board[y][x]

    # create composite for draw: first composite = placed only
    composite = [row[:] for row in placed_buf]
    # overlay ghost (only where placed is empty)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if ghost_buf[y][x] and composite[y][x] == 0:
                composite[y][x] = ghost_buf[y][x].lower() if isinstance(ghost_buf[y][x], str) else ghost_buf[y][x]
    # overlay current piece (bright)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if buf[y][x] and (placed_buf[y][x] == 0):
                composite[y][x] = buf[y][x]

    draw_board(screen, composite, ghost_buf, g.next_piece_type)
    pygame.display.flip()
    clock.tick(60)
