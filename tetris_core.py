# tetris_core.py
import random

WIDTH = 10
HEIGHT = 20

# NES Tetris color-like palette (muted, can be improved later)
PIECE_COLORS = {
    "I": (0, 255, 255),
    "O": (255, 255, 0),
    "T": (128, 0, 128),
    "S": (0, 255, 0),
    "Z": (255, 0, 0),
    "J": (0, 0, 255),
    "L": (255, 128, 0),
}

# Tetromino definitions: 4 rotation states each
PIECES = {
    "I": [
        [(0,1),(1,1),(2,1),(3,1)],
        [(2,0),(2,1),(2,2),(2,3)],
        [(0,2),(1,2),(2,2),(3,2)],
        [(1,0),(1,1),(1,2),(1,3)],
    ],
    "O": [
        [(1,0),(2,0),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(2,1)],
    ],
    "T": [
        [(1,0),(0,1),(1,1),(2,1)],
        [(1,0),(1,1),(2,1),(1,2)],
        [(0,1),(1,1),(2,1),(1,2)],
        [(1,0),(0,1),(1,1),(1,2)],
    ],
    "S": [
        [(1,0),(2,0),(0,1),(1,1)],
        [(1,0),(1,1),(2,1),(2,2)],
        [(1,1),(2,1),(0,2),(1,2)],
        [(0,0),(0,1),(1,1),(1,2)],
    ],
    "Z": [
        [(0,0),(1,0),(1,1),(2,1)],
        [(2,0),(1,1),(2,1),(1,2)],
        [(0,1),(1,1),(1,2),(2,2)],
        [(1,0),(0,1),(1,1),(0,2)],
    ],
    "J": [
        [(0,0),(0,1),(1,1),(2,1)],
        [(1,0),(2,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(0,2),(1,2)],
    ],
    "L": [
        [(2,0),(0,1),(1,1),(2,1)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,1),(0,2)],
        [(0,0),(1,0),(1,1),(1,2)],
    ],
}


class TetrisGame:
    def __init__(self, w=10, h=20):
        self.w = w
        self.h = h
        self.board = [[None for _ in range(w)] for _ in range(h)]
        self.fall_speed = 0.5  # seconds per grid step (level system later)
        self._new_bag()
        self._spawn_piece()

    # --- Piece / bag handling ------------------------------------------------

    def _new_bag(self):
        self.bag = list(PIECES.keys())
        random.shuffle(self.bag)

    def _next_piece(self):
        if not self.bag:
            self._new_bag()
        return self.bag.pop()

    def _spawn_piece(self):
        self.current = self._next_piece()
        self.rotation = 0
        self.x = self.w//2 - 2
        self.y = 0
        if not self._fits(self.x, self.y, self.rotation):
            self.game_over = True
        else:
            self.game_over = False

    # --- Movement & rotation --------------------------------------------------

    def _fits(self, x, y, rot):
        for (dx, dy) in PIECES[self.current][rot]:
            xx = x + dx
            yy = y + dy
            if xx < 0 or xx >= self.w or yy < 0 or yy >= self.h:
                return False
            if self.board[yy][xx]:
                return False
        return True

    def move(self, dx, dy):
        nx = self.x + dx
        ny = self.y + dy
        if self._fits(nx, ny, self.rotation):
            self.x, self.y = nx, ny

    def rotate(self):
        new_rot = (self.rotation + 1) % 4
        if self._fits(self.x, self.y, new_rot):
            self.rotation = new_rot

    # --- Falling logic --------------------------------------------------------

    def fall(self):
        if self._fits(self.x, self.y + 1, self.rotation):
            self.y += 1
        else:
            self._lock_piece()
            self._clear_lines()
            self._spawn_piece()

    def soft_drop(self):
        """Move piece down by one cell if possible, else lock."""
        if self._fits(self.x, self.y + 1, self.rotation):
            self.y += 1
        else:
            self._lock_piece()
            self._clear_lines()
            self._spawn_piece()

    def hard_drop(self):
        while self._fits(self.x, self.y + 1, self.rotation):
            self.y += 1
        self._lock_piece()
        self._clear_lines()
        self._spawn_piece()

    def _lock_piece(self):
        for (dx, dy) in PIECES[self.current][self.rotation]:
            xx = self.x + dx
            yy = self.y + dy
            if 0 <= yy < self.h:
                self.board[yy][xx] = self.current

    def _clear_lines(self):
        new = [row for row in self.board if any(c is None for c in row)]
        cleared = self.h - len(new)
        for _ in range(cleared):
            new.insert(0, [None]*self.w)
        self.board = new

    # --- Buffers for external renderers --------------------------------------

    def get_buffer(self):
        buf = [[None for _ in range(self.w)] for _ in range(self.h)]
        for (dx, dy) in PIECES[self.current][self.rotation]:
            xx = self.x + dx
            yy = int(self.y) + dy
            if 0 <= xx < self.w and 0 <= yy < self.h:
                buf[yy][xx] = self.current
        return buf

    def get_ghost_buffer(self):
        gy = self.y
        while self._fits(self.x, gy+1, self.rotation):
            gy += 1
        buf = [[None for _ in range(self.w)] for _ in range(self.h)]
        for (dx, dy) in PIECES[self.current][self.rotation]:
            xx = self.x + dx
            yy = int(gy) + dy
            if 0 <= xx < self.w and 0 <= yy < self.h:
                buf[yy][xx] = self.current.lower()  # darker shade
        return buf

    def get_preview_overlay(self):
        # Show next piece faint at top row center
        nxt = self.bag[-1] if self.bag else self.current
        shape = PIECES[nxt][0]
        px = self.w//2 - 2
        py = 1
        buf = [[None for _ in range(self.w)] for _ in range(self.h)]
        for (dx, dy) in shape:
            xx = px + dx
            yy = py + dy
            if 0 <= xx < self.w and 0 <= yy < self.h:
                buf[yy][xx] = nxt.lower()
        return buf
