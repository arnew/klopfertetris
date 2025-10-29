# tetris_core.py
# Improved Tetris core: rotation with kick attempts, lock delay, ghost piece and next preview,
# color mapping by piece type. Keeps API simple for renderer.

import random, copy, time

# 4x4 tetromino bitmaps (same as before)
TETROMINOS = {
    'I': [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    'O': [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
    'T': [[0,1,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'J': [[1,0,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'L': [[0,0,1,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'S': [[0,1,1,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
    'Z': [[1,1,0,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
}

# Pleasant palette (R,G,B)
PIECE_COLORS = {
    'I': (0, 240, 240),
    'O': (240, 240, 0),
    'T': (160, 0, 240),
    'J': (0, 0, 240),
    'L': (240, 160, 0),
    'S': (0, 240, 0),
    'Z': (240, 0, 0),
    'X': (120,120,120),  # used for garbage or preview fallback
}

def rotate_cw(shape):
    # rotate 4x4 matrix clockwise
    return [ [shape[3-c][r] for c in range(4)] for r in range(4) ]

class Game:
    def __init__(self, width=10, height=20, level=0, lock_delay=0.5):
        self.width = width
        self.height = height
        self.level = level
        self.lock_delay = lock_delay
        self.reset()

    def reset(self):
        self.board = [[0]*self.width for _ in range(self.height)]
        self.score = 0
        self.lines = 0
        self.bag = []
        self.next_piece_type = None
        self._fill_bag()
        self._spawn_from_bag()
        self.drop_timer = 0.0
        self.drop_delay = self.level_to_delay(self.level)
        self.lock_timer = 0.0
        self.game_over = False
        self.last_cleared = 0

    def level_to_delay(self, level):
        base = 1.0
        return max(0.03, base * (0.8 ** level))

    def _fill_bag(self):
        if not self.bag:
            self.bag = list(TETROMINOS.keys())
            random.shuffle(self.bag)
        if not self.next_piece_type:
            self.next_piece_type = self.bag.pop()

    def _spawn_from_bag(self):
        # ensure next is available
        if not self.bag:
            self.bag = list(TETROMINOS.keys())
            random.shuffle(self.bag)
        # current piece becomes next recorded
        if not self.next_piece_type:
            self.next_piece_type = self.bag.pop()
        self.piece_type = self.next_piece_type
        self.next_piece_type = self.bag.pop() if self.bag else None
        self.piece = copy.deepcopy(TETROMINOS[self.piece_type])
        # spawn near top; NES spawns with slight offset - we use py=-1 so piece can enter
        self.px = self.width//2 - 2
        self.py = -1
        self.lock_timer = 0.0
        # check immediate collision -> game over
        if self.collides():
            self.game_over = True

    def collides(self, px=None, py=None, piece=None):
        px = self.px if px is None else px
        py = self.py if py is None else py
        piece = self.piece if piece is None else piece
        for y in range(4):
            for x in range(4):
                if piece[y][x]:
                    bx = px + x
                    by = py + y
                    if bx < 0 or bx >= self.width:
                        return True
                    if by >= self.height:
                        return True
                    if by >= 0 and self.board[by][bx]:
                        return True
        return False

    # rotation with simple kick attempt list
    def rotate(self):
        newp = rotate_cw(self.piece)
        # basic kick offsets to try (center-ish, L/R, up)
        kicks = [(0,0), (-1,0), (1,0), (-2,0), (2,0), (0,-1), (0,1)]
        for ox, oy in kicks:
            if not self.collides(px=self.px+ox, py=self.py+oy, piece=newp):
                self.piece = newp
                self.px += ox
                self.py += oy
                # rotating resets lock timer (player can move/rotate within lock delay)
                self.lock_timer = 0.0
                return True
        # rotation failed -> no change
        return False

    def move(self, dx):
        if not self.collides(px=self.px+dx):
            self.px += dx
            self.lock_timer = 0.0
            return True
        return False

    def soft_drop(self):
        if not self.collides(py=self.py+1):
            self.py += 1
            # soft drop does not reset lock timer per classic, but we reset for better feel
            self.lock_timer = 0.0
            return True
        return False

    def hard_drop(self):
        # drop until collision then lock
        while not self.collides(py=self.py+1):
            self.py += 1
        self.lock_piece()

    def lock_piece(self):
        for y in range(4):
            for x in range(4):
                if self.piece[y][x]:
                    bx = self.px + x
                    by = self.py + y
                    if 0 <= by < self.height and 0 <= bx < self.width:
                        self.board[by][bx] = self.piece_type  # store piece id for coloring
        cleared = self.clear_lines()
        self.last_cleared = cleared
        self.score += self.score_for_clear(cleared)
        self.lines += cleared
        # spawn next
        self._spawn_from_bag()

    def clear_lines(self):
        newb = [row for row in self.board if any(v==0 for v in row)]
        cleared = self.height - len(newb)
        while len(newb) < self.height:
            newb.insert(0, [0]*self.width)
        self.board = newb
        return cleared

    def score_for_clear(self, n):
        if n==0: return 0
        elif n==1: return 40*(self.level+1)
        elif n==2: return 100*(self.level+1)
        elif n==3: return 300*(self.level+1)
        else: return 1200*(self.level+1)

    def update(self, dt, soft_down=False):
        if self.game_over:
            return
        # gravity timing
        # if soft_down True, accelerate by factor
        self.drop_timer += dt
        delay = self.level_to_delay(self.level) if not soft_down else max(0.02, self.level_to_delay(self.level) * 0.1)
        if self.drop_timer >= delay:
            self.drop_timer = 0.0
            if not self.collides(py=self.py+1):
                self.py += 1
                self.lock_timer = 0.0
            else:
                # piece is resting on something; start/advance lock timer
                self.lock_timer += dt
                if self.lock_timer >= self.lock_delay:
                    self.lock_piece()
                    self.lock_timer = 0.0

    def get_buffer(self):
        """
        Returns a 2D array height x width with:
          0: empty
          'I','O','T',... : filled by placed pieces or current piece
          lowercase for ghost overlay? (we keep types)
        Note: current falling piece is shown with its piece_type.
        """
        buf = [row[:] for row in self.board]
        # place current piece (if within visible rows)
        for y in range(4):
            for x in range(4):
                if self.piece[y][x]:
                    bx = self.px + x
                    by = self.py + y
                    if 0 <= bx < self.width and 0 <= by < self.height:
                        buf[by][bx] = self.piece_type
        return buf

    def get_ghost_y(self):
        """Return the y coordinate for the ghost piece (where it would land)."""
        test_y = self.py
        while not self.collides(py=test_y+1):
            test_y += 1
        return test_y

    def get_ghost_buffer(self):
        """Return a buffer same size, marking ghost positions with piece type but distinguishable by renderer."""
        buf = [[0]*self.width for _ in range(self.height)]
        gy = self.get_ghost_y()
        for y in range(4):
            for x in range(4):
                if self.piece[y][x]:
                    bx = self.px + x
                    by = gy + y
                    if 0 <= bx < self.width and 0 <= by < self.height:
                        buf[by][bx] = self.piece_type
        return buf

    def add_garbage(self, n):
        for _ in range(n):
            hole = random.randrange(0, self.width)
            row = [1]*self.width
            row[hole] = 0
            self.board.pop(0)
            # convert 1→'X' so renderer colors garbage differently (or mapped)
            self.board.append(['X' if v else 0 for v in row])
