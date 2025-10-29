# tetris_core.py
import random, copy, time

TETROMINOS = {
    'I': [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
    'O': [[0,1,1,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
    'T': [[0,1,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'J': [[1,0,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'L': [[0,0,1,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    'S': [[0,1,1,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
    'Z': [[1,1,0,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
}

def rotate_cw(shape):
    return [ [shape[3-c][r] for c in range(4)] for r in range(4) ]

class Game:
    def __init__(self, width=10, height=20, level=0):
        self.width = width
        self.height = height
        self.level = level
        self.reset()

    def reset(self):
        self.board = [[0]*self.width for _ in range(self.height)]
        self.score = 0
        self.lines = 0
        self.bag = []
        self.next_piece()
        self.drop_timer = 0.0
        self.drop_delay = self.level_to_delay(self.level)
        self.game_over = False

    def level_to_delay(self, level):
        # approximate seconds per drop; tune as desired
        base = 1.0
        return max(0.05, base * (0.8 ** level))

    def next_piece(self):
        if not self.bag:
            self.bag = list(TETROMINOS.keys())
            random.shuffle(self.bag)
        self.piece_type = self.bag.pop()
        self.piece = copy.deepcopy(TETROMINOS[self.piece_type])
        self.px = self.width//2 - 2
        self.py = -1  # spawn slightly above
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

    def move(self, dx):
        if not self.collides(px=self.px+dx):
            self.px += dx

    def rotate(self):
        newp = rotate_cw(self.piece)
        if not self.collides(piece=newp):
            self.piece = newp

    def soft_drop(self):
        if not self.collides(py=self.py+1):
            self.py += 1
            return True
        return False

    def hard_drop(self):
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
                        self.board[by][bx] = 1
        cleared = self.clear_lines()
        self.score += self.score_for_clear(cleared)
        self.lines += cleared
        self.next_piece()

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

    def update(self, dt):
        if self.game_over:
            return
        self.drop_timer += dt
        if self.drop_timer >= self.drop_delay:
            if not self.collides(py=self.py+1):
                self.py += 1
            else:
                # piece cannot move down — lock
                self.lock_piece()
            self.drop_timer = 0.0

    def get_buffer(self):
        # return height x width 2D array (0 or 1)
        buf = [row[:] for row in self.board]
        for y in range(4):
            for x in range(4):
                if self.piece[y][x]:
                    bx = self.px + x
                    by = self.py + y
                    if 0 <= bx < self.width and 0 <= by < self.height:
                        buf[by][bx] = 1
        return buf

    # For garbage: append n lines at bottom with one hole per row
    def add_garbage(self, n):
        for _ in range(n):
            hole = random.randrange(0, self.width)
            row = [1]*self.width
            row[hole] = 0
            self.board.pop(0)
            self.board.append(row)
