import pygame, time, math
from sim.tetris_sim import TetrisSim
from rules.tetris_rules import RulesEngine as TetrisRules

# Duplicate utility functions here to avoid circular import.
def build_frame_from_rules(rules_engine):
    w = rules_engine.width
    h = rules_engine.height
    buf = [[None for _ in range(w)] for __ in range(h)]
    bd = rules_engine.get_board()
    for y in range(h):
        for x in range(w):
            buf[y][x] = bd[y][x]
    for (x, y, ch) in rules_engine.get_ghost_cells():
        if 0 <= y < h and 0 <= x < w and buf[y][x] is None:
            buf[y][x] = ch
    for (x, y, ch) in rules_engine.get_current_cells():
        if 0 <= y < h and 0 <= x < w:
            buf[y][x] = ch
    for (x, y, ch) in rules_engine.get_preview_cells():
        if 0 <= y < h and 0 <= x < w and buf[y][x] is None:
            buf[y][x] = ch
    return buf

COLORS_TET = {
    "I": (0,255,255),"O":(255,255,0),"T":(160,0,160),
    "S":(0,255,0),"Z":(255,0,0),"J":(0,0,255),"L":(255,128,0),"X":(120,120,120)
}
def frame_to_rgb(frame, mode):
    h = len(frame); w = len(frame[0])
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            cell = frame[y][x]
            if cell is None:
                row.append((0,0,0))
            else:
                ch = str(cell).upper()
                if str(cell).islower():
                    col = (10,10,10)
                else:
                    col = COLORS_TET.get(ch, (120,120,120))
                row.append(col)
        out.append(row)
    return out

def pastel_fade_color(t):
    r = int(128 + 80 * math.sin(t * 0.2 + 0))
    g = int(128 + 80 * math.sin(t * 0.2 + 2))
    b = int(128 + 80 * math.sin(t * 0.2 + 4))
    return (r, g, b)

def ss_ai_step(sim, dt):
    import random
    if random.random() < 0.1:
        sim.rotate()
    if random.random() < 0.5:
        sim.input.press_left()
    else:
        sim.input.release_left()
    if random.random() < 0.5:
        sim.input.press_right()
    else:
        sim.input.release_right()
    sim.update(dt, soft_hold=True)

def run_screensaver(screen, usb, SS_W, SS_H, last_input_time):
    # Static state for screensaver
    if not hasattr(run_screensaver, "ss_rules"):
        run_screensaver.ss_rules = TetrisRules(SS_W, SS_H)
        run_screensaver.ss_sim = TetrisSim(run_screensaver.ss_rules)
        run_screensaver.ss_PIX = 24
        run_screensaver.ss_pos = [40, 40]
        run_screensaver.ss_vel = [2, 2]
        run_screensaver.ss_box = (SS_W * run_screensaver.ss_PIX, SS_H * run_screensaver.ss_PIX)

    ss_rules = run_screensaver.ss_rules
    ss_sim = run_screensaver.ss_sim
    ss_PIX = run_screensaver.ss_PIX
    ss_pos = run_screensaver.ss_pos
    ss_vel = run_screensaver.ss_vel
    ss_box = run_screensaver.ss_box

    # Handle exit events
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            exit(0)
        elif ev.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION):
            return True  # exit screensaver

    # Move subscreen
    ss_pos[0] += ss_vel[0]
    ss_pos[1] += ss_vel[1]
    if ss_pos[0] <= 0 or ss_pos[0] + ss_box[0] >= screen.get_width():
        ss_vel[0] *= -1
        ss_pos[0] = max(0, min(ss_pos[0], screen.get_width() - ss_box[0]))
    if ss_pos[1] <= 0 or ss_pos[1] + ss_box[1] >= screen.get_height():
        ss_vel[1] *= -1
        ss_pos[1] = max(0, min(ss_pos[1], screen.get_height() - ss_box[1]))

    ss_ai_step(ss_sim, 1/60)

    FRAME_W, FRAME_H = 10, 20
    BOTTLE_PIX = 24
    fade_color = pastel_fade_color(time.time())
    frame_rgb = [[fade_color for _ in range(FRAME_W)] for _ in range(FRAME_H)]

    ss_grid_x = int(round(ss_pos[0] / (screen.get_width() / FRAME_W)))
    ss_grid_y = int(round(ss_pos[1] / (screen.get_height() / FRAME_H)))
    ss_grid_x = max(0, min(FRAME_W - SS_W, ss_grid_x))
    ss_grid_y = max(0, min(FRAME_H - SS_H, ss_grid_y))

    ss_frame = build_frame_from_rules(ss_rules)
    ss_rgb = frame_to_rgb(ss_frame, "tetris")
    for y in range(SS_H):
        for x in range(SS_W):
            gx = ss_grid_x + x
            gy = ss_grid_y + y
            if 0 <= gx < FRAME_W and 0 <= gy < FRAME_H:
                frame_rgb[gy][gx] = ss_rgb[y][x]

    if usb:
        from renderer.usb_frame import send_frame
        send_frame(usb, frame_rgb, FRAME_W, FRAME_H)

    screen.fill((0,0,0))
    for y in range(FRAME_H):
        for x in range(FRAME_W):
            r,g,b = frame_rgb[y][x]
            pygame.draw.rect(
                screen, (r,g,b),
                (x*BOTTLE_PIX, y*BOTTLE_PIX, BOTTLE_PIX-1, BOTTLE_PIX-1)
            )
    pygame.display.flip()
    return False  # stay in screensaver
