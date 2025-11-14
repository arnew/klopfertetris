import pygame

# Move these utility functions here from main.py to break the circular dependency.
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
COLORS_TRI = {
    "I": (20,20,255), "L": (255,20,16), "D": (20,255,20), "x": (12,12,12)
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
                    if mode == "tetris":
                        col = COLORS_TET.get(ch, (120,120,120))
                    else:
                        col = COLORS_TRI.get(ch, (120,120,120))
                row.append(col)
        out.append(row)
    return out

# Avoid name clash with possible installed 'gameplay' modules
def run_gameplay(screen, sim, rules, mode, usb, last_input_time):
    PIX = 24 if mode == "tetris" else 48
    small_font = pygame.font.SysFont(None, 20)
    hat_left = False
    hat_right = False
    hat_down = False

    # Handle events
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            exit(0)
        elif ev.type == pygame.KEYDOWN:
            last_input_time = pygame.time.get_ticks() / 1000.0
            if ev.key == pygame.K_ESCAPE:
                pygame.quit()
                exit(0)
            elif ev.key == pygame.K_LEFT:
                sim.input.press_left()
            elif ev.key == pygame.K_RIGHT:
                sim.input.press_right()
            elif ev.key == pygame.K_UP:
                sim.rotate()
            elif ev.key == pygame.K_SPACE:
                sim.hard_drop()
            elif ev.key == pygame.K_DOWN:
                sim.soft_drop()
        elif ev.type == pygame.KEYUP:
            if ev.key == pygame.K_LEFT:
                sim.input.release_left()
            elif ev.key == pygame.K_RIGHT:
                sim.input.release_right()
        elif ev.type == pygame.JOYBUTTONDOWN:
            last_input_time = pygame.time.get_ticks() / 1000.0
            if ev.button == 0:
                sim.rotate()
            elif ev.button == 1:
                sim.hard_drop()
            elif ev.button == 2:
                sim.soft_drop()
            elif ev.button == 3:
                sim.rotate()
        elif ev.type == pygame.JOYBUTTONUP:
            pass
        elif ev.type == pygame.JOYHATMOTION:
            last_input_time = pygame.time.get_ticks() / 1000.0
            hat_x, hat_y = ev.value
            if hat_x < 0:
                sim.input.press_left()
                hat_left = True
            elif hat_x > 0:
                sim.input.press_right()
                hat_right = True
            else:
                if hat_left:
                    sim.input.release_left()
                    hat_left = False
                if hat_right:
                    sim.input.release_right()
                    hat_right = False
            if hat_y < 0:
                sim.soft_drop()
                hat_down = True
            else:
                if hat_down:
                    hat_down = False
            if hat_y > 0:
                sim.rotate()

    keys = pygame.key.get_pressed()
    soft = keys[pygame.K_DOWN] or hat_down

    sim.update(1/60, soft_hold=soft)

    if sim.is_game_over:
        return False, last_input_time

    frame = build_frame_from_rules(rules)
    rgb = frame_to_rgb(frame, mode)

    if usb:
        from renderer.usb_frame import send_frame
        send_frame(usb, rgb, rules.width, rules.height)

    screen.fill((8,8,8))
    for y in range(rules.height):
        for x in range(rules.width):
            r,g,b = rgb[y][x]
            pygame.draw.rect(screen, (r,g,b), (x*PIX, y*PIX, PIX-1, PIX-1))
    text = small_font.render(f"Mode: {mode}", True, (200,200,200))
    screen.blit(text, (rules.width*PIX + 10, 10))
    pygame.display.flip()
    return True, last_input_time
