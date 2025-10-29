# rules/tetris_rules.py
# Tetris rules engine (SRS-like rotation, board, lock helpers)
from copy import deepcopy

# Piece shapes as 4x4 boolean maps (rotation state 0)
BASE_PIECES = {
    "I": [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    "O": [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
    "T": [[0,1,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    "J": [[1,0,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    "L": [[0,0,1,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    "S": [[0,1,1,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
    "Z": [[1,1,0,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
}

def rotate_cw(mat):
    return [[mat[3-c][r] for c in range(4)] for r in range(4)]

# build rotations for each piece
PIECES = {}
for k, v in BASE_PIECES.items():
    rots = []
    cur = deepcopy(v)
    for _ in range(4):
        rots.append(cur)
        cur = rotate_cw(cur)
    PIECES[k] = rots

# SRS kicks (simplified canonical tables)
SRS_KICKS = {
    # (from,to): [(x,y), ...]
    (0,1): [(0,0),(-1,0),(-1,1),(0,-2),(-1,-2)],
    (1,0): [(0,0),(1,0),(1,-1),(0,2),(1,2)],
    (1,2): [(0,0),(-1,0),(-1,1),(0,-2),(-1,-2)],
    (2,1): [(0,0),(1,0),(1,-1),(0,2),(1,2)],
    (2,3): [(0,0),(1,0),(1,1),(0,-2),(1,-2)],
    (3,2): [(0,0),(-1,0),(-1,-1),(0,2),(-1,2)],
    (3,0): [(0,0),(1,0),(1,1),(0,-2),(1,-2)],
    (0,3): [(0,0),(-1,0),(-1,-1),(0,2),(-1,2)],
}
SRS_KICKS_I = {
    (0,1): [(0,0),(-2,0),(1,0),(-2,-1),(1,2)],
    (1,0): [(0,0),(2,0),(-1,0),(2,1),(-1,-2)],
    (1,2): [(0,0),(-1,0),(2,0),(-1,2),(2,-1)],
    (2,1): [(0,0),(1,0),(-2,0),(1,-2),(-2,1)],
    (2,3): [(0,0),(2,0),(-1,0),(2,1),(-1,-2)],
    (3,2): [(0,0),(-2,0),(1,0),(-2,-1),(1,2)],
    (3,0): [(0,0),(1,0),(-2,0),(1,-2),(-2,1)],
    (0,3): [(0,0),(-1,0),(2,0),(-1,2),(2,-1)],
}

class RulesEngine:
    def __init__(self, width=10, height=20):
        self.width = width
        self.height = height
        self.board = [[None for _ in range(width)] for __ in range(height)]
        self.bag = []
        self.current = None
        self.rotation = 0
        self.x = 0
        self.y = 0
        self.next_piece = None
        self._refill_bag()
        self.spawn_piece()

    def _refill_bag(self):
        import random
        if not self.bag:
            self.bag = list(PIECES.keys())
            random.shuffle(self.bag)

    def spawn_piece(self):
        self._refill_bag()
        if self.next_piece is None:
            self.current = self.bag.pop()
            self._refill_bag()
            self.next_piece = self.bag.pop()
        else:
            self.current = self.next_piece
            self._refill_bag()
            self.next_piece = self.bag.pop()
        self.rotation = 0
        self.x = (self.width // 2) - 2
        self.y = -1  # spawn slightly above visible area

    def fits(self, x, y, rot):
        # check piece placed at (x,y) with rotation rot (0..3)
        shape = PIECES[self.current][rot]
        for ry in range(4):
            for rx in range(4):
                if shape[ry][rx]:
                    bx = x + rx
                    by = y + ry
                    if bx < 0 or bx >= self.width or by >= self.height:
                        return False
                    if by >= 0 and self.board[by][bx] is not None:
                        return False
        return True

    def try_rotate(self):
        new_rot = (self.rotation + 1) % 4
        kicks = SRS_KICKS_I if self.current == "I" else SRS_KICKS
        table = kicks.get((self.rotation, new_rot), [(0,0)])
        for ox, oy in table:
            if self.fits(self.x + ox, self.y + oy, new_rot):
                self.rotation = new_rot
                self.x += ox
                self.y += oy
                return True
        return False

    def lock_piece(self):
        shape = PIECES[self.current][self.rotation]
        for ry in range(4):
            for rx in range(4):
                if shape[ry][rx]:
                    bx = self.x + rx
                    by = self.y + ry
                    if 0 <= by < self.height and 0 <= bx < self.width:
                        self.board[by][bx] = self.current
        # spawn next piece afterwards
        self.spawn_piece()

    def clear_lines(self):
        newb = [row for row in self.board if any(cell is None for cell in row)]
        cleared = self.height - len(newb)
        while len(newb) < self.height:
            newb.insert(0, [None for _ in range(self.width)])
        self.board = newb
        return cleared

    # accessors for rendering convenience
    def get_board(self):
        return self.board

    def get_current_cells(self):
        out = []
        shape = PIECES[self.current][self.rotation]
        for ry in range(4):
            for rx in range(4):
                if shape[ry][rx]:
                    out.append((self.x + rx, self.y + ry, self.current))
        return out

    def get_ghost_cells(self):
        gy = self.y
        while self.fits(self.x, gy + 1, self.rotation):
            gy += 1
        out = []
        shape = PIECES[self.current][self.rotation]
        for ry in range(4):
            for rx in range(4):
                if shape[ry][rx]:
                    out.append((self.x + rx, gy + ry, self.current.lower()))
        return out

    def get_preview_cells(self):
        # light preview at top center
        piece = self.next_piece
        if piece is None:
            return []
        shape = PIECES[piece][0]
        px = (self.width // 2) - 2
        py = 0
        out = []
        for ry in range(4):
            for rx in range(4):
                if shape[ry][rx]:
                    out.append((px + rx, py + ry, piece.lower()))
        return out
