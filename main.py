# main.py
import json, time, os, sys
from tetris_core import Game
from renderer.usb_frame import USBFrameRenderer
from renderer.pygame_display import PygameRenderer
from net.network import NetworkNode
from input_handler import InputHandler

CONFIG_PATH = "config.json"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
    return cfg

def choose_renderer(cfg):
    usb_dev = cfg.get("usb_frame_device")
    if usb_dev:
        r = USBFrameRenderer(usb_dev, width=10, height=20)
        if r.available():
            print("Using USB frame renderer")
            return r
    # fallback to CRAP UDP renderer omitted for brevity; use pygame
    print("Falling back to pygame renderer")
    return PygameRenderer(width=10, height=20, cell=20)

def main():
    cfg = load_config()
    player_id = cfg.get("player_id","P")
    player_name = cfg.get("player_name","Player")
    preferred_peer = cfg.get("preferred_peer")
    accept_garbage = cfg.get("accept_garbage","preferred")
    level = cfg.get("default_level",0)

    renderer = choose_renderer(cfg)
    netnode = NetworkNode(player_id, player_name, port=cfg.get("broadcast_port",50000), bcast_addr=cfg.get("broadcast_iface","<broadcast>"))
    netnode.start()

    game = Game(width=10, height=20, level=level)
    inputh = InputHandler()

    # on_garbage callback
    def on_garbage(from_id, to_id, lines):
        # apply if target is ALL or matches this player OR accept_garbage = all or preferred and from preferred
        if accept_garbage == "off":
            return
        if to_id == "ALL" or to_id == player_id:
            if accept_garbage == "all":
                game.add_garbage(lines)
            elif accept_garbage == "preferred" and from_id == preferred_peer:
                game.add_garbage(lines)
    netnode.on_garbage = on_garbage

    last = time.time()
    print("Starting main loop. Controls: arrow keys, space hard drop, enter start.")
    while True:
        now = time.time()
        dt = now - last
        last = now

        # simple start screen/team selection on startup
        # For brevity, start immediately; extend later to full menu
        actions = inputh.poll()
        if actions.get("quit"):
            print("Quitting.")
            break
        if actions.get("rotate"):
            game.rotate()
        if actions.get("left"):
            game.move(-1)
        if actions.get("right"):
            game.move(1)
        if actions.get("soft"):
            game.soft_drop()
        if actions.get("hard"):
            game.hard_drop()

        game.update(dt)
        buf = game.get_buffer()
        renderer.render(buf)

        # when lines cleared (we updated game.lines in lock), send garbage to preferred peer
        # simplistic: if cleared >=2 -> send cleared-1 garbage lines to peer
        # For a proper reaction, keep previous lines count
        # (We implement a simple rule: every time lines increased, send lines-1 to preferred peer)
        # For simplicity, not implemented here — extend as needed.

        time.sleep(0.01)

if __name__ == "__main__":
    main()
