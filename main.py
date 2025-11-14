# main.py
import argparse, time, pygame, math
from rules.tetris_rules import RulesEngine as TetrisRules
from rules.tritris_rules import TritrisRules
from sim.tetris_sim import TetrisSim
from renderer.usb_frame import try_open, send_frame

from gameplay import run_gameplay
from screensaver import run_screensaver

# Ensure this file is not named the same as a library/module in your Python path.
# If you still get import errors, try renaming 'gameplay.py' and 'screensaver.py' to something more unique,
# e.g. 'klopfer_gameplay.py' and 'klopfer_screensaver.py', and update the imports here accordingly:
# from klopfer_gameplay import run_gameplay
# from klopfer_screensaver import run_screensaver

DEFAULT_MODE = "tetris"  # or "tritris"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["tetris","tritris"], default=DEFAULT_MODE)
    args = parser.parse_args()

    mode = args.mode
    if mode == "tetris":
        rules = TetrisRules(10,20)
    else:
        rules = TritrisRules(4,5)

    sim = TetrisSim(rules)
    usb = try_open()
    print("USB device:", "found" if usb else "none")

    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for js in joysticks:
        js.init()
        print(f"Gamepad detected: {js.get_name()}")

    PIX = 24 if mode=="tetris" else 48
    screen = pygame.display.set_mode((rules.width*PIX + 160, rules.height*PIX))
    pygame.display.set_caption(f"{mode} - hybrid renderer")
    clock = pygame.time.Clock()

    # Screensaver state
    screensaver_active = False
    SCREENSAVER_TIMEOUT = 30.0
    last_input_time = time.time()
    game_active = False

    # Subscreen Tetris for screensaver
    SS_W, SS_H = 6, 15

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        now = time.time()

        # Screensaver activation
        if not screensaver_active and not game_active and (now - last_input_time > SCREENSAVER_TIMEOUT):
            screensaver_active = True

        if screensaver_active:
            # Returns True if screensaver should exit (on user input)
            screensaver_active = not run_screensaver(
                screen, usb, SS_W, SS_H, last_input_time
            )
            if not screensaver_active:
                game_active = True
                last_input_time = time.time()
            continue

        if not game_active:
            screensaver_active = True
            continue

        # Returns True if game is still running, False if game over
        game_active, last_input_time = run_gameplay(
            screen, sim, rules, mode, usb, last_input_time
        )

    pygame.quit()

if __name__ == "__main__":
    main()
