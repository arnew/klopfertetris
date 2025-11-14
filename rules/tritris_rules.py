# rules/tritris_rules.py
# Tritris rules: small triominoes for a 4x5 board. API mirrors RulesEngine above.

TRIOMINOES = {
    "I": [  # horizontal base rotation then vertical
        [(0,1),(1,1),(2,1)],
        [(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1)],
        [(1,0),(1,1),(1,2)],
    ],
    "L": [
        [(0,0),(0,1),(1,1)],
        [(0,1),(1,1),(0,2)],
        [(0,1),(1,1),(1,2)],
        [(1,0),(1,1),(0,1)],
    ],
#    "O2":[  # small 2x2 block (behaves like tetromino O but trimmed)
#        [(0,0),(1,0),(0,1)],  # we treat as 3-block L-ish or 2x2 truncated
#        [(0,0),(1,0),(0,1)],
#        [(0,0),(1,0),(0,1)],
#        [(0,0),(1,0),(0,1)],
#    ],
    # NEW DOMINO — replaces O2
    "D": [
        [(0,0),(1,0)],                    # horizontal
        [(0,0),(0,1)],                    # vertical
        [(0,0),(1,0)],                    # horizontal again
        [(0,0),(0,1)],                    # vertical again
    ],
}

class TritrisRules:
    def __init__(self, width=4, height=5):
        self.width = width
        self.height = height
        self.board = [[None for _ in range(width)] for __ in range(height)]
        self.bag = []
        self.current = None
        self.rotation = 0
        self.x = 0
        self.y = 0
        self.next_piece = None
        self.game_over_on_spawn = False
        self._refill_bag()
        self.spawn_piece()

    def _refill_bag(self):
        import random
        if not self.bag:
            self.bag = list(TRIOMINOES.keys())
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
        # spawn near top center (triomino shapes assumed in 3x3 box)
        self.x = (self.width // 2) - 1
        self.y = 0
        # Game over detection: if the new piece doesn't fit at spawn
        if not self.fits(self.x, self.y, self.rotation):
            self.game_over_on_spawn = True

    def fits(self, x, y, rot):
        shape = TRIOMINOES[self.current][rot]
        for (dx, dy) in shape:
            bx = x + dx
            by = y + dy
            if bx < 0 or bx >= self.width or by < 0 or by >= self.height:
                return False
            if self.board[by][bx] is not None:
                return False
        return True

    def try_rotate(self):
        new_rot = (self.rotation + 1) % 4
        # small kicks: center, left, right
        kicks = [(0,0),(-1,0),(1,0),(0,-1)]
        for ox, oy in kicks:
            if self.fits(self.x + ox, self.y + oy, new_rot):
                self.rotation = new_rot
                self.x += ox
                self.y += oy
                return True
        return False

    def lock_piece(self):
        shape = TRIOMINOES[self.current][self.rotation]
        for (dx, dy) in shape:
            bx = self.x + dx
            by = self.y + dy
            if 0 <= by < self.height and 0 <= bx < self.width:
                self.board[by][bx] = self.current
        self.spawn_piece()

    def clear_lines(self):
        newb = [row for row in self.board if any(cell is None for cell in row)]
        cleared = self.height - len(newb)
        while len(newb) < self.height:
            newb.insert(0, [None for _ in range(self.width)])
        self.board = newb
        return cleared

    def get_board(self):
        return self.board

    def get_current_cells(self):
        out = []
        shape = TRIOMINOES[self.current][self.rotation]
        for (dx, dy) in shape:
            out.append((self.x + dx, self.y + dy, self.current))
        return out

    def get_ghost_cells(self):
        gy = self.y
        while self.fits(self.x, gy + 1, self.rotation):
            gy += 1
        out = []
        shape = TRIOMINOES[self.current][self.rotation]
        for (dx, dy) in shape:
            out.append((self.x + dx, gy + dy, self.current.lower()))
        return out

    def get_preview_cells(self):
        piece = self.next_piece
        if piece is None:
            return []
        shape = TRIOMINOES[piece][0]
        px = (self.width // 2) - 1
        py = 0
        out = []
        for (dx, dy) in shape:
            out.append((px + dx, py + dy, piece.lower()))
        return out

    def is_game_over(self):
        return self.game_over_on_spawn
