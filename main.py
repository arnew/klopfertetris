# main.py
import argparse, time, pygame
from rules.tetris_rules import RulesEngine as TetrisRules
from rules.tritris_rules import TritrisRules
from sim.tetris_sim import TetrisSim
from renderer.usb_frame import try_open, send_frame
import math

DEFAULT_MODE = "tetris"  # or "tritris"

COLORS_TET = {
    "I": (0,255,255),"O":(255,255,0),"T":(160,0,160),
    "S":(0,255,0),"Z":(255,0,0),"J":(0,0,255),"L":(255,128,0),"X":(120,120,120)
}

COLORS_TRI = {
    "I": (20,20,255), "L": (255,20,16), "D": (20,255,20), "x": (12,12,12)
}

def build_frame_from_rules(rules_engine):
    w = rules_engine.width
    h = rules_engine.height
    # start with placed board
    buf = [[None for _ in range(w)] for __ in range(h)]
    bd = rules_engine.get_board()
    for y in range(h):
        for x in range(w):
            buf[y][x] = bd[y][x]
    # overlay ghost
    for (x,y,ch) in rules_engine.get_ghost_cells():
        if 0 <= y < h and 0 <= x < w and buf[y][x] is None:
            buf[y][x] = ch  # lower-case indicates ghost
    # overlay current
    for (x,y,ch) in rules_engine.get_current_cells():
        if 0 <= y < h and 0 <= x < w:
            buf[y][x] = ch
    # overlay preview
    for (x,y,ch) in rules_engine.get_preview_cells():
        if 0 <= y < h and 0 <= x < w and buf[y][x] is None:
            buf[y][x] = ch
    return buf

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
                # ghost/preview if lowercase
                if str(cell).islower():
                    # dim color
                    col = (10,10,10)
                else:
                    if mode == "tetris":
                        col = COLORS_TET.get(ch, (120,120,120))
                    else:
                        col = COLORS_TRI.get(ch, (120,120,120))
                row.append(col)
        out.append(row)
    return out

def pastel_fade_color(t):
    # t: float, seconds
    # Returns a pastel RGB tuple, smoothly cycling
    # Use sine waves with phase offsets for R, G, B
    r = int(128 + 80 * math.sin(t * 0.2 + 0))
    g = int(128 + 80 * math.sin(t * 0.2 + 2))
    b = int(128 + 80 * math.sin(t * 0.2 + 4))
    return (r, g, b)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["tetris","tritris"], default=DEFAULT_MODE)
    args = parser.parse_args()

    mode = args.mode
    if mode == "tetris":
        rules = TetrisRules(10,20)
        colors = COLORS_TET
    else:
        rules = TritrisRules(4,5)
        colors = COLORS_TRI

    sim = TetrisSim(rules)
    # try open USB device
    usb = try_open()
    print("USB device:", "found" if usb else "none")

    # pygame setup (for mirror or fallback)
    pygame.init()
    # Initialize joysticks/gamepads
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for js in joysticks:
        js.init()
        print(f"Gamepad detected: {js.get_name()}")

    PIX = 24 if mode=="tetris" else 48
    screen = pygame.display.set_mode((rules.width*PIX + 160, rules.height*PIX))
    pygame.display.set_caption(f"{mode} - hybrid renderer")
    clock = pygame.time.Clock()

    running = True
    hat_left = False
    hat_right = False
    hat_down = False

    # --- Screensaver state ---
    screensaver_active = False
    screensaver_timer = 0.0
    SCREENSAVER_TIMEOUT = 30.0  # seconds of inactivity before screensaver
    last_input_time = time.time()
    game_active = False

    # --- Subscreen Tetris for screensaver ---
    SS_W, SS_H = 6, 15
    ss_rules = TetrisRules(SS_W, SS_H)
    ss_sim = TetrisSim(ss_rules)
    ss_PIX = 16
    ss_pos = [40, 40]
    ss_vel = [2, 2]  # pixels per frame
    ss_box = (SS_W * ss_PIX, SS_H * ss_PIX)

    # Placeholder for AI step interface
    def ss_ai_step(dt):
        # To be replaced with real AI logic
        # For now, just soft drop and random moves
        import random
        if random.random() < 0.1:
            ss_sim.rotate()
        if random.random() < 0.5:
            ss_sim.input.press_left()
        else:
            ss_sim.input.release_left()
        if random.random() < 0.5:
            ss_sim.input.press_right()
        else:
            ss_sim.input.release_right()
        ss_sim.update(dt, soft_hold=True)

    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 20)

    while running:
        dt = clock.tick(60) / 1000.0

        # --- Screensaver activation logic ---
        now = time.time()
        if not screensaver_active and not game_active and (now - last_input_time > SCREENSAVER_TIMEOUT):
            screensaver_active = True
            # Reset subscreen Tetris
            ss_rules.__init__(SS_W, SS_H)
            ss_sim.reset()
            # Randomize start position and direction
            import random
            ss_pos[0] = random.randint(0, max(0, screen.get_width() - ss_box[0]))
            ss_pos[1] = random.randint(0, max(0, screen.get_height() - ss_box[1]))
            ss_vel[0] = random.choice([-2, 2])
            ss_vel[1] = random.choice([-2, 2])

        # --- Screensaver mode ---
        if screensaver_active:
            # Screensaver mode: run AI Tetris in a moving subscreen
            exit_screensaver = False
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION):
                    exit_screensaver = True
            if exit_screensaver:
                screensaver_active = False
                game_active = True  # allow game to start after screensaver
                last_input_time = time.time()
                # Clear event queue to avoid double-processing input
                pygame.event.clear()
                continue
            # Move subscreen
            ss_pos[0] += ss_vel[0]
            ss_pos[1] += ss_vel[1]
            if ss_pos[0] <= 0 or ss_pos[0] + ss_box[0] >= screen.get_width():
                ss_vel[0] *= -1
                ss_pos[0] = max(0, min(ss_pos[0], screen.get_width() - ss_box[0]))
            if ss_pos[1] <= 0 or ss_pos[1] + ss_box[1] >= screen.get_height():
                ss_vel[1] *= -1
                ss_pos[1] = max(0, min(ss_pos[1], screen.get_height() - ss_box[1]))
            # AI step
            ss_ai_step(dt)

            # --- Compose a 20x10 RGB frame for both pygame and USB ---
            FRAME_W, FRAME_H = 10, 20
            BOTTLE_PIX = 20  # for pygame display only

            # Fade background color
            fade_color = pastel_fade_color(time.time())

            # Start with pastel background frame
            frame_rgb = [[fade_color for _ in range(FRAME_W)] for _ in range(FRAME_H)]

            # Place the small Tetris frame into the big frame at the right position
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

            # Send to USB if available
            if usb:
                send_frame(usb, frame_rgb, FRAME_W, FRAME_H)

            # --- Render to pygame using the same frame ---
            screen.fill((0,0,0))
            for y in range(FRAME_H):
                for x in range(FRAME_W):
                    r,g,b = frame_rgb[y][x]
                    pygame.draw.rect(
                        screen, (r,g,b),
                        (x*BOTTLE_PIX, y*BOTTLE_PIX, BOTTLE_PIX-1, BOTTLE_PIX-1)
                    )
            pygame.display.flip()
            continue

        # --- Startup/game over screen state ---
        if not game_active:
            # No text, just screensaver
            screensaver_active = True
            continue

        # --- Main game loop ---
        # events
        soft = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                last_input_time = time.time()
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key == pygame.K_LEFT:
                    sim.input.press_left()
                elif ev.key == pygame.K_RIGHT:
                    sim.input.press_right()
                elif ev.key == pygame.K_UP:
                    sim.rotate()
                elif ev.key == pygame.K_SPACE:
                    sim.hard_drop()
                elif ev.key == pygame.K_DOWN:
                    # call soft drop once now; autorepeat will be handled by sim update
                    sim.soft_drop()
            elif ev.type == pygame.KEYUP:
                if ev.key == pygame.K_LEFT:
                    sim.input.release_left()
                elif ev.key == pygame.K_RIGHT:
                    sim.input.release_right()
            elif ev.type == pygame.JOYBUTTONDOWN:
                last_input_time = time.time()
                # Map some buttons generically (may need adjustment for your controller)
                if ev.button == 0:  # e.g. A
                    sim.rotate()
                elif ev.button == 1:  # e.g. B
                    sim.hard_drop()
                elif ev.button == 2:  # e.g. X
                    sim.soft_drop()
                elif ev.button == 3:  # e.g. Y
                    sim.rotate()
            elif ev.type == pygame.JOYBUTTONUP:
                # No action needed for button up in this mapping
                pass
            elif ev.type == pygame.JOYHATMOTION:
                last_input_time = time.time()
                # D-pad/hat input
                hat_x, hat_y = ev.value
                # Left/right
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
                # Down/soft drop
                if hat_y < 0:
                    sim.soft_drop()
                    hat_down = True
                else:
                    if hat_down:
                        hat_down = False
                # Up/rotate
                if hat_y > 0:
                    sim.rotate()

        keys = pygame.key.get_pressed()
        soft = keys[pygame.K_DOWN] or hat_down

        # update sim
        sim.update(dt, soft_hold=soft)

        # If game over, switch to game over screen
        if sim.is_game_over:
            game_active = False
            continue

        # render frame from rules engine
        frame = build_frame_from_rules(rules)
        rgb = frame_to_rgb(frame, mode)

        # send to USB if available
        if usb:
            send_frame(usb, rgb, rules.width, rules.height)

        # pygame mirror
        # draw
        screen.fill((8,8,8))
        for y in range(rules.height):
            for x in range(rules.width):
                r,g,b = rgb[y][x]
                pygame.draw.rect(screen, (r,g,b), (x*PIX, y*PIX, PIX-1, PIX-1))
        # draw preview box
        text = small_font.render(f"Mode: {mode}", True, (200,200,200))
        screen.blit(text, (rules.width*PIX + 10, 10))
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
